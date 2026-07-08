"""
Order service — vendor-agnostic placement, admin-brokered routing, delivery.

Flow (per the client brief):
  1. Buyer places an order for product *concepts* (a variant like Shoes/Blue/US-8), NOT a
     specific vendor. Because many vendors list the same concept at different prices, the
     order total is stored as a RANGE (estimated_min_total .. estimated_max_total). No stock
     is touched yet.
  2. The area admin views candidate vendors who actually have that concept in stock, along
     with price / delivery-time / priority / stock, and assigns one.
  3. On assignment the price is FINALIZED (vendor price + commission), stock is reserved, and
     the money-flow breakdown is filled. The vendor accepts (confirm) or rejects (restock +
     re-route). Delivery is status-based, proof required to mark delivered.
"""
from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from ecommerce.models import (
    Cart, Delivery, Order, OrderItem, OrderStatusLog, OrderVendorAssignment, ProductVariant,
)
from ecommerce.services import catalog as catalog_service
from ecommerce.services import notifications
from ecommerce.services.inventory import apply_movement

TWO_PLACES = Decimal('0.01')


def generate_order_no():
    now = timezone.now()
    prefix = f"SHN-{now:%Y%m%d}"
    count = Order.objects.all_with_deleted().filter(order_no__startswith=prefix).count()
    return f"{prefix}-{count + 1:06d}"


def _resolve_area_node(delivery_address):
    if not delivery_address:
        return None
    mapping = (
        delivery_address.node_mappings
        .select_related('node', 'level')
        .order_by('-level__sort_order')
        .first()
    )
    return mapping.node if mapping else None


def _area_prefix(order):
    addr = order.delivery_address
    code = addr.residential_code if addr else None
    return catalog_service.area_prefix(code) if code else None


def effective_delivery_time(product):
    """Product-level delivery time, else the store's default."""
    if product.delivery_time_minutes:
        return product.delivery_time_minutes
    store = getattr(product.business_family, 'store_setting', None)
    return store.default_delivery_time_minutes if store else 0


def _concept_variants(concept_key, area_prefix=None, in_stock_qty=None):
    """Active variants (across vendors) matching a concept, optionally filtered by area/stock."""
    qs = (
        ProductVariant.objects
        .filter(concept_key=concept_key, is_deleted=False, status=ProductVariant.STATUS_ACTIVE,
                product__status='active', product__is_deleted=False)
        .select_related('product', 'product__template', 'product__business_family')
        .exclude(product__business_family__store_setting__is_online=False)
    )
    if area_prefix:
        qs = qs.filter(product__area_code__startswith=area_prefix)
    if in_stock_qty is not None:
        qs = qs.filter(stock_qty__gte=in_stock_qty)
    return qs


def _final_price(variant):
    template = variant.product.template
    return (Decimal(variant.price) + template.commission_for(variant.price)).quantize(TWO_PLACES)


def log_status(order, status, actor_context=OrderStatusLog.ACTOR_SYSTEM, user=None, note=None):
    return OrderStatusLog.objects.create(
        order=order, status=status, actor_context=actor_context, changed_by=user, note=note)


def _set_status(order, status, actor_context, user=None, note=None, extra_fields=None):
    order.status = status
    fields = ['status', 'updated_at']
    if extra_fields:
        for key, value in extra_fields.items():
            setattr(order, key, value)
            fields.append(key)
    order.save(update_fields=fields)
    log_status(order, status, actor_context, user, note)
    return order


# =====================================================================================
# Placement — price RANGE, no stock movement
# =====================================================================================
@transaction.atomic
def place_order_from_cart(user, cart, *, delivery_address=None, note=None):
    if cart.status != Cart.STATUS_ACTIVE:
        raise ValueError("This cart has already been used to place an order.")

    items = list(cart.items.select_related(
        'variant', 'variant__product', 'variant__product__template'))
    if not items:
        raise ValueError("Cart is empty.")

    order = Order.objects.create(
        order_no=generate_order_no(),
        buyer=user,
        area_node=_resolve_area_node(delivery_address),
        delivery_address=delivery_address,
        status=Order.STATUS_PLACED,
        placed_at=timezone.now(),
        note=note,
    )
    area_prefix = _area_prefix(order)

    est_min_total = Decimal('0')
    est_max_total = Decimal('0')
    for item in items:
        rep = item.variant                       # the representative variant the buyer selected
        product = rep.product
        qty = item.quantity
        concept = rep.concept_key

        candidates = list(_concept_variants(concept, area_prefix=area_prefix))
        prices = [_final_price(v) for v in candidates] or [_final_price(rep)]
        est_min = (min(prices) * qty).quantize(TWO_PLACES)
        est_max = (max(prices) * qty).quantize(TWO_PLACES)
        est_min_total += est_min
        est_max_total += est_max

        attrs = {
            av.attribute.name: av.display
            for av in rep.attribute_values.select_related('attribute', 'option', 'unit')
        }
        primary_image = product.images.filter(is_primary=True).first() or product.images.first()
        OrderItem.objects.create(
            order=order, variant=None, template=product.template, concept_key=concept,
            product_name=product.name, variant_sku=rep.sku, attributes_snapshot=attrs,
            image_url=primary_image.image.url if primary_image else None, quantity=qty,
            estimated_min_price=est_min, estimated_max_price=est_max)

    order.estimated_min_total = est_min_total.quantize(TWO_PLACES)
    order.estimated_max_total = est_max_total.quantize(TWO_PLACES)
    order.save(update_fields=['estimated_min_total', 'estimated_max_total', 'updated_at'])

    log_status(order, Order.STATUS_PLACED, OrderStatusLog.ACTOR_BUYER, user)
    _set_status(order, Order.STATUS_PENDING_ASSIGNMENT, OrderStatusLog.ACTOR_SYSTEM, user,
                note="Awaiting area admin assignment.")

    cart.status = Cart.STATUS_ORDERED
    cart.save(update_fields=['status', 'updated_at'])

    ctx = {'order_no': order.order_no,
           'estimated_min': str(order.estimated_min_total),
           'estimated_max': str(order.estimated_max_total)}
    notifications.notify('ecommerce.order_placed', user, ctx)
    notifications.notify_area_admins('ecommerce.order_new_area', order.area_node, ctx)
    return order


# =====================================================================================
# Routing — candidate vendors + finalize on assignment
# =====================================================================================
def candidate_vendors(order):
    """
    Vendors who can fulfil EVERY line of the order (matching concept + enough stock),
    with the attributes the admin routes on: price, delivery time, priority, stock.
    """
    area_prefix = _area_prefix(order)
    items = list(order.items.all())
    if not items:
        return []

    # business_id -> {variant per concept}. Start from the first line, then intersect.
    per_business = {}
    for idx, item in enumerate(items):
        matches = {}
        for v in _concept_variants(item.concept_key, area_prefix=area_prefix, in_stock_qty=item.quantity):
            matches.setdefault(v.product.business_family_id, v)
        if idx == 0:
            per_business = {bid: {items[0].id: v} for bid, v in matches.items()}
        else:
            per_business = {
                bid: {**data, item.id: matches[bid]}
                for bid, data in per_business.items() if bid in matches
            }
        if not per_business:
            return []

    results = []
    qty_by_item = {item.id: item.quantity for item in items}
    for bid, item_variants in per_business.items():
        vendor_total = Decimal('0')
        commission_total = Decimal('0')
        delivery_fee = Decimal('0')
        delivery_time = 0
        seen_products = set()
        business = None
        for item_id, variant in item_variants.items():
            qty = qty_by_item[item_id]
            business = variant.product.business_family
            template = variant.product.template
            vendor_total += Decimal(variant.price) * qty
            commission_total += template.commission_for(variant.price) * qty
            delivery_time = max(delivery_time, effective_delivery_time(variant.product))
            if variant.product_id not in seen_products:
                delivery_fee += Decimal(variant.product.delivery_fee)
                seen_products.add(variant.product_id)
        final_total = (vendor_total + commission_total + delivery_fee).quantize(TWO_PLACES)
        results.append({
            'business_family_id': bid,
            'business_name': business.name,
            'priority_score': business.priority_score,
            'vendor_subtotal': str(vendor_total.quantize(TWO_PLACES)),
            'commission_amount': str(commission_total.quantize(TWO_PLACES)),
            'delivery_fee': str(delivery_fee.quantize(TWO_PLACES)),
            'final_total': str(final_total),
            'delivery_time_minutes': delivery_time,
            'in_stock': True,
        })
    results.sort(key=lambda c: (-c['priority_score'], float(c['final_total'])))
    return results


def _vendor_variant_for(concept_key, business_family, qty, area_prefix=None):
    return (
        _concept_variants(concept_key, area_prefix=area_prefix, in_stock_qty=qty)
        .filter(product__business_family=business_family)
        .first()
    )


@transaction.atomic
def assign_to_vendor(order, business_family, admin, note=None):
    if order.status not in (Order.STATUS_PLACED, Order.STATUS_PENDING_ASSIGNMENT,
                            Order.STATUS_ASSIGNED, Order.STATUS_REJECTED):
        raise ValueError(f"Order in status '{order.status}' cannot be assigned.")

    area_prefix = _area_prefix(order)
    items = list(order.items.all())

    # Validate the vendor can fulfil every line, and gather the matching variants.
    bindings = []
    for item in items:
        variant = _vendor_variant_for(item.concept_key, business_family, item.quantity, area_prefix)
        if not variant:
            raise ValueError(
                f"{business_family.name} does not have enough stock for '{item.product_name}'.")
        bindings.append((item, variant))

    # If the order was already assigned to someone (offered), release that reservation first.
    if order.is_price_final and order.business_family_id:
        _release_reservation(order, actor=OrderStatusLog.ACTOR_ADMIN, user=admin)

    OrderVendorAssignment.objects.filter(
        order=order, status=OrderVendorAssignment.OFFERED
    ).update(status=OrderVendorAssignment.REASSIGNED, responded_at=timezone.now())

    vendor_subtotal = Decimal('0')
    commission_total = Decimal('0')
    tax_total = Decimal('0')
    delivery_products = {}
    for item, variant in bindings:
        template = variant.product.template
        qty = item.quantity
        vendor_unit = Decimal(variant.price)
        commission_unit = template.commission_for(vendor_unit)
        final_unit = (vendor_unit + commission_unit).quantize(TWO_PLACES)

        item.variant = variant
        item.variant_sku = variant.sku
        item.vendor_unit_price = vendor_unit.quantize(TWO_PLACES)
        item.commission_type = template.commission_type
        item.commission_value = Decimal(template.commission_value)
        item.commission_unit_amount = commission_unit
        item.final_unit_price = final_unit
        item.line_total = (final_unit * qty).quantize(TWO_PLACES)
        item.save()

        vendor_subtotal += vendor_unit * qty
        commission_total += commission_unit * qty
        tax_total += (vendor_unit * qty * Decimal(variant.product.tax_rate) / Decimal('100'))
        delivery_products[variant.product_id] = Decimal(variant.product.delivery_fee)

        apply_movement(variant, 'sale', -qty, reason=f"Order {order.order_no}",
                       reference_type='order', reference_id=order.id, user=admin)

    delivery_fee = sum(delivery_products.values(), Decimal('0'))
    subtotal = (vendor_subtotal + commission_total).quantize(TWO_PLACES)
    total = (subtotal + tax_total + delivery_fee).quantize(TWO_PLACES)

    order.business_family = business_family
    order.assigned_admin = admin
    order.vendor_subtotal = vendor_subtotal.quantize(TWO_PLACES)
    order.commission_amount = commission_total.quantize(TWO_PLACES)
    order.subtotal = subtotal
    order.tax_amount = tax_total.quantize(TWO_PLACES)
    order.delivery_fee = Decimal(delivery_fee).quantize(TWO_PLACES)
    order.total_amount = total
    order.is_price_final = True
    order.save()

    assignment = OrderVendorAssignment.objects.create(
        order=order, business_family=business_family, area_node=order.area_node,
        assigned_by=admin, status=OrderVendorAssignment.OFFERED, note=note)
    _set_status(order, Order.STATUS_ASSIGNED, OrderStatusLog.ACTOR_ADMIN, admin,
                note=f"Assigned to {business_family.name}; price finalized at {total}.")
    notifications.notify_business_members(
        'ecommerce.order_assigned_vendor', business_family, {'order_no': order.order_no})
    return assignment


def _release_reservation(order, actor=OrderStatusLog.ACTOR_SYSTEM, user=None):
    """Restock a finalized order's reserved variants and clear the money-flow fields."""
    for item in order.items.select_related('variant'):
        if item.variant_id:
            apply_movement(item.variant, 'return', item.quantity,
                           reason=f"Release {order.order_no}", reference_type='order',
                           reference_id=order.id, user=user)
            item.variant = None
            item.vendor_unit_price = Decimal('0')
            item.commission_unit_amount = Decimal('0')
            item.final_unit_price = Decimal('0')
            item.line_total = Decimal('0')
            item.save()
    order.business_family = None
    order.vendor_subtotal = Decimal('0')
    order.commission_amount = Decimal('0')
    order.subtotal = Decimal('0')
    order.tax_amount = Decimal('0')
    order.delivery_fee = Decimal('0')
    order.total_amount = Decimal('0')
    order.is_price_final = False
    order.save()


@transaction.atomic
def vendor_accept(order, business_family, user=None):
    assignment = (
        order.vendor_assignments
        .filter(business_family=business_family, status=OrderVendorAssignment.OFFERED)
        .order_by('-created_at').first()
    )
    if not assignment:
        raise ValueError("No open offer for this vendor.")

    assignment.status = OrderVendorAssignment.ACCEPTED
    assignment.responded_at = timezone.now()
    assignment.save(update_fields=['status', 'responded_at', 'updated_at'])

    _set_status(order, Order.STATUS_ACCEPTED, OrderStatusLog.ACTOR_MERCHANT, user,
                note=f"Accepted by {business_family.name}.",
                extra_fields={'assigned_at': timezone.now()})
    notifications.notify('ecommerce.order_accepted', order.buyer, {'order_no': order.order_no})
    return order


@transaction.atomic
def vendor_reject(order, business_family, user=None, note=None):
    assignment = (
        order.vendor_assignments
        .filter(business_family=business_family, status=OrderVendorAssignment.OFFERED)
        .order_by('-created_at').first()
    )
    if not assignment:
        raise ValueError("No open offer for this vendor.")

    assignment.status = OrderVendorAssignment.REJECTED
    assignment.responded_at = timezone.now()
    assignment.note = note or assignment.note
    assignment.save(update_fields=['status', 'responded_at', 'note', 'updated_at'])

    # Restock and drop the finalized price so the admin can re-route (back to a range).
    _release_reservation(order, actor=OrderStatusLog.ACTOR_MERCHANT, user=user)
    _set_status(order, Order.STATUS_PENDING_ASSIGNMENT, OrderStatusLog.ACTOR_MERCHANT, user,
                note="Rejected; returned to admin for re-routing.")
    notifications.notify('ecommerce.order_rejected', order.assigned_admin,
                         {'order_no': order.order_no, 'vendor': business_family.name})
    notifications.notify_area_admins('ecommerce.order_rejected', order.area_node,
                                     {'order_no': order.order_no})
    return order


# =====================================================================================
# Delivery
# =====================================================================================
def _is_business_member(business_family, agent):
    from user.models import BusinessFamilyMember
    if not business_family or not agent:
        return False
    return BusinessFamilyMember.objects.filter(
        business_family=business_family, user=agent, is_active=True).exists()


@transaction.atomic
def assign_agent(order, agent, user=None):
    if order.status not in (Order.STATUS_ACCEPTED, Order.STATUS_AGENT_ASSIGNED):
        raise ValueError("Order must be accepted before assigning a delivery agent.")
    if not _is_business_member(order.business_family, agent):
        raise ValueError("Delivery agent must be an active employee of the fulfilling vendor.")
    delivery, _ = Delivery.objects.get_or_create(order=order)
    delivery.agent = agent
    delivery.status = Delivery.STATUS_ASSIGNED
    delivery.assigned_at = timezone.now()
    delivery.save()
    _set_status(order, Order.STATUS_AGENT_ASSIGNED, OrderStatusLog.ACTOR_MERCHANT, user,
                note="Delivery agent assigned.")
    notifications.notify('ecommerce.agent_assigned', agent, {'order_no': order.order_no})
    notifications.notify('ecommerce.order_agent_assigned', order.buyer, {'order_no': order.order_no})
    return delivery


@transaction.atomic
def agent_accept_delivery(order, user=None):
    delivery, _ = Delivery.objects.get_or_create(order=order)
    delivery.status = Delivery.STATUS_ACCEPTED
    delivery.accepted_at = timezone.now()
    delivery.save()
    log_status(order, order.status, OrderStatusLog.ACTOR_AGENT, user, note="Agent accepted delivery.")
    return delivery


@transaction.atomic
def update_delivery_status(order, delivery_status, user=None, actor=OrderStatusLog.ACTOR_AGENT,
                           otp_code=None, proof_image=None):
    valid = {c[0] for c in Delivery.STATUS_CHOICES}
    if delivery_status not in valid:
        raise ValueError(f"Invalid delivery status '{delivery_status}'.")

    delivery, _ = Delivery.objects.get_or_create(order=order)

    if delivery_status == Delivery.STATUS_DELIVERED:
        if proof_image is None and not delivery.proof_image:
            raise ValueError("Proof of delivery (image) is required to mark the order delivered.")

    delivery.status = delivery_status
    now = timezone.now()
    order_status_map = {
        Delivery.STATUS_PICKED_UP: Order.STATUS_PICKED_UP,
        Delivery.STATUS_IN_TRANSIT: Order.STATUS_IN_TRANSIT,
        Delivery.STATUS_DELIVERED: Order.STATUS_DELIVERED,
    }
    if delivery_status == Delivery.STATUS_PICKED_UP:
        delivery.picked_up_at = now
    elif delivery_status == Delivery.STATUS_DELIVERED:
        delivery.delivered_at = now
        if proof_image is not None:
            delivery.proof_image = proof_image
        if otp_code:
            delivery.otp_verified = (otp_code == delivery.otp_code) if delivery.otp_code else True
    delivery.save()

    order_status = order_status_map.get(delivery_status)
    if order_status:
        extra = {}
        if order_status == Order.STATUS_DELIVERED:
            extra['payment_status'] = Order.PAYMENT_PAID  # placeholder until wallet exists
        _set_status(order, order_status, actor, user, extra_fields=extra or None)
        notifications.notify(f'ecommerce.order_{order_status}', order.buyer,
                             {'order_no': order.order_no})
    return delivery


@transaction.atomic
def cancel_order(order, user=None, actor=OrderStatusLog.ACTOR_BUYER, note=None):
    if order.status in (Order.STATUS_DELIVERED, Order.STATUS_COMPLETED,
                        Order.STATUS_CANCELLED, Order.STATUS_RETURNED):
        raise ValueError(f"Order in status '{order.status}' cannot be cancelled.")

    # Restock only if a vendor was assigned (stock was reserved).
    if order.is_price_final:
        for item in order.items.select_related('variant'):
            if item.variant_id:
                apply_movement(item.variant, 'return', item.quantity,
                               reason=f"Cancel {order.order_no}", reference_type='order',
                               reference_id=order.id, user=user)
    extra = {}
    if order.payment_status == Order.PAYMENT_PAID:
        extra['payment_status'] = Order.PAYMENT_REFUNDED
    _set_status(order, Order.STATUS_CANCELLED, actor, user, note=note, extra_fields=extra or None)
    notifications.notify('ecommerce.order_cancelled', order.buyer, {'order_no': order.order_no})
    if order.business_family:
        notifications.notify_business_members(
            'ecommerce.order_cancelled', order.business_family, {'order_no': order.order_no})
    return order
