"""
Seed sample e-commerce data so the Postman collection has something to hit.

Idempotent: safe to run repeatedly. Creates an admin, two merchants (each with a
BusinessFamily), a buyer, a delivery agent, the global attribute/unit library, a 'Shoes'
template (10% commission), and one product per merchant (same product, different prices,
same area) so the area feed shows a price range.

    python manage.py seed_ecommerce
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from ecommerce.models import (
    Attribute, AttributeOption, MerchantStoreSetting, Product, ProductTemplate,
    ProductVariant, ProductVariantGroup, ProductVariantGroupValue, StockMovement,
    TemplateAttribute, Unit, UnitType, VariantAttributeValue,
)
from ecommerce.services import catalog as catalog_service
from ecommerce.services.inventory import apply_movement
from notification.models import NotificationCategory, NotificationTemplate
from user.models import BusinessFamily, BusinessFamilyMember, DesignationType, User

PASSWORD = 'pass1234'
AREA_CODE = '01-05-03-09'

# (template_name, title, content) — Django template syntax for placeholders.
NOTIFICATION_TEMPLATES = [
    ('ecommerce.order_placed', 'Order placed', 'Your order {{ order_no }} was placed successfully. Total: {{ total_amount }}.'),
    ('ecommerce.order_new_area', 'New order in your area', 'A new order {{ order_no }} needs to be assigned to a vendor.'),
    ('ecommerce.order_assigned_vendor', 'New order to fulfil', 'Order {{ order_no }} has been offered to your store. Please accept or reject.'),
    ('ecommerce.order_accepted', 'Order accepted', 'Good news! Your order {{ order_no }} was accepted and is being prepared.'),
    ('ecommerce.order_rejected', 'Order needs re-routing', 'Order {{ order_no }} was rejected by {{ vendor }} and needs re-assignment.'),
    ('ecommerce.agent_assigned', 'Delivery assigned to you', 'You have been assigned delivery for order {{ order_no }}.'),
    ('ecommerce.order_agent_assigned', 'Out for delivery soon', 'A delivery agent has been assigned to your order {{ order_no }}.'),
    ('ecommerce.order_picked_up', 'Order picked up', 'Your order {{ order_no }} has been picked up.'),
    ('ecommerce.order_in_transit', 'Order on the way', 'Your order {{ order_no }} is on the way.'),
    ('ecommerce.order_delivered', 'Order delivered', 'Your order {{ order_no }} has been delivered. Enjoy!'),
    ('ecommerce.order_cancelled', 'Order cancelled', 'Order {{ order_no }} has been cancelled.'),
]


class Command(BaseCommand):
    help = 'Seed sample e-commerce data (idempotent).'

    def _user(self, contact_no, name, **extra):
        user = User.all_objects.filter(contact_no=contact_no).first()
        if user:
            return user
        return User.objects.create_user(contact_no=contact_no, password=PASSWORD, full_name=name, **extra)

    def _business(self, name, contact_no, email, owner, designation):
        biz = BusinessFamily.objects.filter(contact_no=contact_no).first()
        if not biz:
            biz = BusinessFamily.objects.create(
                name=name, contact_no=contact_no, email=email, business_type='private_limited')
        BusinessFamilyMember.objects.get_or_create(
            business_family=biz, user=owner, defaults={'self_designation_type': designation})
        MerchantStoreSetting.objects.get_or_create(
            business_family=biz, defaults={'is_online': True, 'is_open': True})
        return biz

    def _product(self, business, sku, price, template, ta_color, ta_size, opt, us_unit, created_by):
        if Product.objects.filter(business_family=business, sku=sku).exists():
            return Product.objects.get(business_family=business, sku=sku)
        product = Product.objects.create(
            business_family=business, template=template, name='Nike Air', sku=sku,
            base_price=Decimal('1000.00'), tax_rate=Decimal('0'), delivery_fee=Decimal('40.00'),
            preparation_time_minutes=30, area_code=AREA_CODE,
            grouping_key=catalog_service.build_grouping_key(template.id, 'Nike Air'),
            created_by=created_by,
        )
        group = ProductVariantGroup.objects.create(product=product, label='Blue', sort_order=1)
        ProductVariantGroupValue.objects.create(
            variant_group=group, template_attribute=ta_color, attribute=ta_color.attribute,
            value_text='Blue')
        variant = ProductVariant.objects.create(
            product=product, variant_group=group, sku=f'{sku}-BL-8', price=Decimal(price),
            compare_at_price=Decimal('1500.00'), stock_qty=0, low_stock_threshold=2, is_default=True)
        VariantAttributeValue.objects.create(
            variant=variant, template_attribute=ta_color, attribute=ta_color.attribute, value_text='Blue')
        VariantAttributeValue.objects.create(
            variant=variant, template_attribute=ta_size, attribute=ta_size.attribute,
            option=opt, unit=us_unit)
        apply_movement(variant, StockMovement.PURCHASE, 10, reason='Seed stock', user=created_by)
        return product

    def _seed_notifications(self):
        category, _ = NotificationCategory.objects.get_or_create(
            name='ecommerce', defaults={'display_name': 'E-Commerce'})
        for name, title, content in NOTIFICATION_TEMPLATES:
            NotificationTemplate.objects.get_or_create(
                name=name,
                defaults={'category': category, 'title': title, 'content': content,
                          'channels': ['in_app', 'push']})

    @transaction.atomic
    def handle(self, *args, **options):
        self._seed_notifications()

        # --- users ---
        admin = self._user('+919000000001', 'Seed Admin', is_staff=True, is_superuser=True, is_verified=True)
        merchant_a = self._user('+919000000002', 'Merchant A')
        merchant_b = self._user('+919000000003', 'Merchant B')
        buyer = self._user('+919000000004', 'Buyer')
        agent = self._user('+919000000005', 'Delivery Agent')

        designation, _ = DesignationType.objects.get_or_create(
            name='owner', defaults={'display_name': 'Owner', 'post_no': 1})

        biz_a = self._business('Shoe Store A', '+919111111111', 'a@shop.com', merchant_a, designation)
        biz_b = self._business('Shoe Store B', '+919222222222', 'b@shop.com', merchant_b, designation)

        # --- global library ---
        unit_type, _ = UnitType.objects.get_or_create(
            code='shoe_size', defaults={'name': 'Shoe Size System'})
        us_unit, _ = Unit.objects.get_or_create(
            unit_type=unit_type, name='US', defaults={'is_base': True, 'sort_order': 1})
        Unit.objects.get_or_create(unit_type=unit_type, name='UK', defaults={'sort_order': 2})
        Unit.objects.get_or_create(unit_type=unit_type, name='EU', defaults={'sort_order': 3})

        color, _ = Attribute.objects.get_or_create(
            code='color', defaults={'name': 'Color', 'input_type': 'text'})
        size, _ = Attribute.objects.get_or_create(
            code='size', defaults={'name': 'Size', 'input_type': 'dropdown', 'unit_type': unit_type})
        for i, val in enumerate(['7', '8', '9', '10'], start=1):
            AttributeOption.objects.get_or_create(
                attribute=size, value=val, defaults={'display_value': val, 'sort_order': i})
        opt8 = AttributeOption.objects.get(attribute=size, value='8')

        # --- template (10% commission) ---
        template, _ = ProductTemplate.objects.get_or_create(
            code='shoes',
            defaults={'name': 'Shoes', 'commission_type': 'percent', 'commission_value': Decimal('10.00')})
        ta_color, _ = TemplateAttribute.objects.get_or_create(
            template=template, attribute=color,
            defaults={'is_required': True, 'is_variant_defining': True, 'is_image_defining': True,
                      'sort_order': 1})
        ta_size, _ = TemplateAttribute.objects.get_or_create(
            template=template, attribute=size,
            defaults={'is_required': True, 'is_variant_defining': True, 'default_unit': us_unit,
                      'sort_order': 2})

        # --- products (same product, two vendors, same area, different price) ---
        self._product(biz_a, 'NIKE-A', '1200.00', template, ta_color, ta_size, opt8, us_unit, merchant_a)
        self._product(biz_b, 'NIKE-B', '1000.00', template, ta_color, ta_size, opt8, us_unit, merchant_b)

        self.stdout.write(self.style.SUCCESS('\nSeed complete.'))
        self.stdout.write('  Password for all users: ' + PASSWORD)
        self.stdout.write(f'  Admin     : +919000000001  (id {admin.id})')
        self.stdout.write(f'  Merchant A: +919000000002  (id {merchant_a.id})  -> BusinessFamily id {biz_a.id}')
        self.stdout.write(f'  Merchant B: +919000000003  (id {merchant_b.id})  -> BusinessFamily id {biz_b.id}')
        self.stdout.write(f'  Buyer     : +919000000004  (id {buyer.id})')
        self.stdout.write(f'  Agent     : +919000000005  (id {agent.id})')
        self.stdout.write(f'  Template  : Shoes (id {template.id})   Area code: {AREA_CODE}')
