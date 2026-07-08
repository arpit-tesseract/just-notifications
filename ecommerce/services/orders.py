"""
Order service: place-from-cart with the full money-flow breakdown, admin-brokered area
routing, delivery transitions, and cancellation/restock.

Money flow (no wallet yet, but fully recorded on the order):
    total_amount = subtotal + tax + delivery_fee - discount
    subtotal     = vendor_subtotal + commission_amount
    vendor_subtotal + delivery_fee -> owed to the fulfilling VENDOR
    commission_amount              -> SHASHAN platform revenue
"""
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from ecommerce.models import (
    Cart, Delivery, Order, OrderItem, OrderStatusLog, OrderVendorAssignment,
)
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


def log_status(order, status, actor_context=OrderStatusLog.ACTOR_SYSTEM, user=None, note=None):
    return OrderStatusLog.objects.create(
        order=order, status=status, actor_context=actor_context, changed_by=user, note=note,
    )


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


@transaction.atomic
def place_order_from_cart(user, cart, *, delivery_address=None, note=None):
    """Convert an active cart into an order, locking prices and decrementing stock."""
    items = list(
        cart.items.select_related('variant', 'variant__product', 'variant__product__template')
    )
    if not items:
        raise ValueError("Cart is empty.")

    vendor_subtotal = Decimal('0')
    commission_amount = Decimal('0')
    subtotal = Decimal('0')
    tax_amount = Decimal('0')
    delivery_products = {}
    line_specs = []

    for item in items:
        variant = item.variant
        product = variant.product
        template = product.template
        qty = item.quantity

        if variant.stock_qty < qty:
            raise ValueError(f"Insufficient stock for '{variant.sku}'.")

        vendor_unit = Decimal(variant.price)
        commission_unit = template.commission_for(vendor_unit)
        final_unit = (vendor_unit + commission_unit).quantize(TWO_PLACES)
        line_total = (final_unit * qty).quantize(TWO_PLACES)
        line_tax = (vendor_unit * qty * Decimal(product.tax_rate) / Decimal('100')).quantize(TWO_PLACES)

        vendor_subtotal += (vendor_unit * qty)
        commission_amount += (commission_unit * qty)
        subtotal += line_total
        tax_amount += line_tax
        delivery_products[product.id] = Decimal(product.delivery_fee)

        attrs = {
            av.attribute.name: av.display
            for av in variant.attribute_values.select_related('attribute', 'option', 'unit')
        }
        primary_image = product.images.filter(is_primary=True).first() or product.images.first()
        line_specs.append({
            'variant': variant,
            'product_name': product.name,
            'variant_sku': variant.sku,
            'attributes_snapshot': attrs,
            'image_url': primary_image.image.url if primary_image else None,
            'quantity': qty,
            'vendor_unit_price': vendor_unit.quantize(TWO_PLACES),
            'commission_type': template.commission_type,
            'commission_value': Decimal(template.commission_value),
            'commission_unit_amount': commission_unit,
            'final_unit_price': final_unit,
            'line_total': line_total,
        })

    delivery_fee = sum(delivery_products.values(), Decimal('0'))
    total_amount = (subtotal + tax_amount + delivery_fee).quantize(TWO_PLACES)

    order = Order.objects.create(
        order_no=generate_order_no(),
        buyer=user,
        area_node=_resolve_area_node(delivery_address),
        listing_business_family=cart.business_family,
        delivery_address=delivery_address,
        vendor_subtotal=vendor_subtotal.quantize(TWO_PLACES),
        commission_amount=commission_amount.quantize(TWO_PLACES),
        subtotal=subtotal.quantize(TWO_PLACES),
        tax_amount=tax_amount.quantize(TWO_PLACES),
        delivery_fee=Decimal(delivery_fee).quantize(TWO_PLACES),
        total_amount=total_amount,
        status=Order.STATUS_PLACED,
        placed_at=timezone.now(),
        note=note,
    )

    for spec in line_specs:
        variant = spec.pop('variant')
        OrderItem.objects.create(order=order, variant=variant, **spec)
        apply_movement(
            variant, 'sale', -spec['quantity'],
            reason=f"Order {order.order_no}", reference_type='order', reference_id=order.id, user=user,
        )

    log_status(order, Order.STATUS_PLACED, OrderStatusLog.ACTOR_BUYER, user)
    _set_status(order, Order.STATUS_PENDING_ASSIGNMENT, OrderStatusLog.ACTOR_SYSTEM, user,
                note="Awaiting area admin assignment.")

    cart.status = Cart.STATUS_ORDERED
    cart.save(update_fields=['status', 'updated_at'])

    ctx = {'order_no': order.order_no, 'total_amount': str(order.total_amount)}
    notifications.notify('ecommerce.order_placed', user, ctx)
    notifications.notify_area_admins('ecommerce.order_new_area', order.area_node, ctx)
    return order


@transaction.atomic
def assign_to_vendor(order, business_family, admin, note=None):
    if order.status not in (Order.STATUS_PLACED, Order.STATUS_PENDING_ASSIGNMENT,
                            Order.STATUS_ASSIGNED, Order.STATUS_REJECTED):
        raise ValueError(f"Order in status '{order.status}' cannot be assigned.")

    OrderVendorAssignment.objects.filter(
        order=order, status=OrderVendorAssignment.OFFERED
    ).update(status=OrderVendorAssignment.REASSIGNED, responded_at=timezone.now())

    assignment = OrderVendorAssignment.objects.create(
        order=order,
        business_family=business_family,
        area_node=order.area_node,
        assigned_by=admin,
        status=OrderVendorAssignment.OFFERED,
        note=note,
    )
    _set_status(order, Order.STATUS_ASSIGNED, OrderStatusLog.ACTOR_ADMIN, admin,
                note=f"Offered to {business_family.name}.", extra_fields={'assigned_admin': admin})
    notifications.notify_business_members(
        'ecommerce.order_assigned_vendor', business_family, {'order_no': order.order_no})
    return assignment


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

    _set_status(
        order, Order.STATUS_ACCEPTED, OrderStatusLog.ACTOR_MERCHANT, user,
        note=f"Accepted by {business_family.name}.",
        extra_fields={'business_family': business_family, 'assigned_at': timezone.now()},
    )
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

    _set_status(order, Order.STATUS_PENDING_ASSIGNMENT, OrderStatusLog.ACTOR_MERCHANT, user,
                note="Rejected; returned to admin for re-routing.")
    notifications.notify(
        'ecommerce.order_rejected', order.assigned_admin,
        {'order_no': order.order_no, 'vendor': business_family.name})
    notifications.notify_area_admins(
        'ecommerce.order_rejected', order.area_node, {'order_no': order.order_no})
    return order


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
    # SRS: delivery is handled by employees of the fulfilling merchant company.
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

    # Proof of delivery is mandatory to mark an order 'delivered'.
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
        notifications.notify(
            f'ecommerce.order_{order_status}', order.buyer, {'order_no': order.order_no})
    return delivery


@transaction.atomic
def cancel_order(order, user=None, actor=OrderStatusLog.ACTOR_BUYER, note=None):
    if order.status in (Order.STATUS_DELIVERED, Order.STATUS_COMPLETED,
                        Order.STATUS_CANCELLED, Order.STATUS_RETURNED):
        raise ValueError(f"Order in status '{order.status}' cannot be cancelled.")

    for item in order.items.select_related('variant'):
        apply_movement(
            item.variant, 'return', item.quantity,
            reason=f"Cancel {order.order_no}", reference_type='order', reference_id=order.id, user=user,
        )
    extra = {}
    if order.payment_status == Order.PAYMENT_PAID:
        extra['payment_status'] = Order.PAYMENT_REFUNDED
    _set_status(order, Order.STATUS_CANCELLED, actor, user, note=note, extra_fields=extra or None)
    notifications.notify('ecommerce.order_cancelled', order.buyer, {'order_no': order.order_no})
    if order.business_family:
        notifications.notify_business_members(
            'ecommerce.order_cancelled', order.business_family, {'order_no': order.order_no})
    return order
