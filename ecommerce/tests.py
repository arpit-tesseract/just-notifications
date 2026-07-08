"""
End-to-end tests for the e-commerce module.

Covers: admin config + dynamic form-schema, merchant nested product/variant creation,
inventory movements, area-based vendor-hidden feed with price range + commission,
cart -> place order (money-flow breakdown), admin area-routing (assign/accept/reject),
delivery -> payment, and cancellation restock.
"""
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase


def _proof_file():
    return SimpleUploadedFile('proof.jpg', b'proof-bytes', content_type='image/jpeg')

from ecommerce.models import (
    AttributeOption, Cart, Order, OrderVendorAssignment, Product, ProductVariant,
    StockMovement, TemplateAttribute,
)
from user.models import BusinessFamily, BusinessFamilyMember, DesignationType, User


def make_user(contact_no, name, **extra):
    return User.objects.create_user(contact_no=contact_no, password='pass1234', full_name=name, **extra)


def make_business(name, contact_no, email):
    return BusinessFamily.objects.create(
        name=name, contact_no=contact_no, email=email, business_type='private_limited')


@override_settings(ECOMMERCE_NOTIFICATIONS_ENABLED=False)
class EcommerceFlowTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = make_user('+919000000001', 'Admin', is_staff=True, is_superuser=True)
        cls.merchant_a = make_user('+919000000002', 'Merchant A')
        cls.merchant_b = make_user('+919000000003', 'Merchant B')
        cls.buyer = make_user('+919000000004', 'Buyer')
        cls.agent = make_user('+919000000005', 'Agent')

        cls.designation = DesignationType.objects.create(name='owner', display_name='Owner', post_no=1)

        cls.biz_a = make_business('Shoe Store A', '+919111111111', 'a@shop.com')
        cls.biz_b = make_business('Shoe Store B', '+919222222222', 'b@shop.com')
        BusinessFamilyMember.objects.create(
            business_family=cls.biz_a, user=cls.merchant_a, self_designation_type=cls.designation)
        BusinessFamilyMember.objects.create(
            business_family=cls.biz_b, user=cls.merchant_b, self_designation_type=cls.designation)
        # Delivery agent is an employee of vendor A (SRS: delivery handled by company employees).
        BusinessFamilyMember.objects.create(
            business_family=cls.biz_a, user=cls.agent, self_designation_type=cls.designation)

    # ---- helpers -------------------------------------------------------------------
    def _build_config(self):
        """Admin builds the global library + Shoes template (10% commission)."""
        self.client.force_authenticate(self.admin)

        ut = self.client.post('/api/ecommerce/unit-types/',
                              {'name': 'Shoe Size System', 'code': 'shoe_size'}, format='json')
        self.assertEqual(ut.status_code, status.HTTP_201_CREATED, ut.data)
        self.unit_type_id = ut.data['id']
        us = self.client.post('/api/ecommerce/units/',
                              {'unit_type': self.unit_type_id, 'name': 'US', 'is_base': True}, format='json')
        self.us_id = us.data['id']
        self.client.post('/api/ecommerce/units/',
                         {'unit_type': self.unit_type_id, 'name': 'UK'}, format='json')

        color = self.client.post('/api/ecommerce/attributes/',
                                 {'name': 'Color', 'code': 'color', 'input_type': 'text'}, format='json')
        self.color_attr_id = color.data['id']
        size = self.client.post('/api/ecommerce/attributes/', {
            'name': 'Size', 'code': 'size', 'input_type': 'dropdown',
            'unit_type': self.unit_type_id,
            'options': [{'value': '7'}, {'value': '8'}, {'value': '9'}],
        }, format='json')
        self.size_attr_id = size.data['id']
        self.opt8_id = AttributeOption.objects.get(attribute_id=self.size_attr_id, value='8').id

        template = self.client.post('/api/ecommerce/templates/', {
            'name': 'Shoes', 'code': 'shoes',
            'commission_type': 'percent', 'commission_value': '10.00',
            'template_attributes': [
                {'attribute': self.color_attr_id, 'is_required': True,
                 'is_variant_defining': True, 'is_image_defining': True, 'sort_order': 1},
                {'attribute': self.size_attr_id, 'is_required': True,
                 'is_variant_defining': True, 'default_unit': self.us_id, 'sort_order': 2},
            ],
        }, format='json')
        self.assertEqual(template.status_code, status.HTTP_201_CREATED, template.data)
        self.template_id = template.data['id']
        tas = TemplateAttribute.objects.filter(template_id=self.template_id)
        self.ta_color = tas.get(attribute_id=self.color_attr_id)
        self.ta_size = tas.get(attribute_id=self.size_attr_id)

    def _product_payload(self, business_id, sku, price):
        return {
            'business_family': business_id, 'template': self.template_id,
            'name': 'Nike Air', 'sku': sku, 'base_price': '1000.00', 'tax_rate': '0',
            'delivery_fee': '40.00', 'preparation_time_minutes': 30,
            'variant_groups': [{
                'label': 'Blue', 'sort_order': 1,
                'values': [{'template_attribute': self.ta_color.id, 'value_text': 'Blue'}],
                'variants': [{
                    'sku': f'{sku}-BL-8', 'price': price, 'stock_qty': 10, 'low_stock_threshold': 2,
                    'attribute_values': [
                        {'template_attribute': self.ta_color.id, 'value_text': 'Blue'},
                        {'template_attribute': self.ta_size.id, 'option': self.opt8_id, 'unit': self.us_id},
                    ],
                }],
            }],
        }

    # ---- tests ---------------------------------------------------------------------
    def test_01_form_schema_reflects_config(self):
        self._build_config()
        res = self.client.get(f'/api/ecommerce/templates/{self.template_id}/form-schema/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['commission_type'], 'percent')
        fields = {f['name']: f for f in res.data['fields']}
        self.assertEqual(fields['Color']['input_type'], 'text')
        self.assertTrue(fields['Color']['is_image_defining'])
        self.assertEqual(len(fields['Size']['options']), 3)
        self.assertEqual(len(fields['Size']['units']), 2)

    def test_02_merchant_creates_product_with_variants_and_stock(self):
        self._build_config()
        self.client.force_authenticate(self.merchant_a)
        res = self.client.post('/api/ecommerce/products/',
                               self._product_payload(self.biz_a.id, 'NIKE-001', '1200.00'), format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        product = Product.objects.get(id=res.data['id'])
        variant = product.variants.get()
        self.assertEqual(variant.stock_qty, 10)
        self.assertEqual(variant.attribute_values.count(), 2)
        self.assertTrue(StockMovement.objects.filter(
            variant=variant, movement_type=StockMovement.PURCHASE, quantity_delta=10).exists())

    def test_03_merchant_cannot_create_for_others_business(self):
        self._build_config()
        self.client.force_authenticate(self.merchant_a)
        res = self.client.post('/api/ecommerce/products/',
                               self._product_payload(self.biz_b.id, 'X-1', '1200.00'), format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_04_feed_groups_vendors_with_price_range_incl_commission(self):
        self._build_config()
        self.client.force_authenticate(self.merchant_a)
        self.client.post('/api/ecommerce/products/',
                         self._product_payload(self.biz_a.id, 'NIKE-A', '1200.00'), format='json')
        self.client.force_authenticate(self.merchant_b)
        self.client.post('/api/ecommerce/products/',
                         self._product_payload(self.biz_b.id, 'NIKE-B', '1000.00'), format='json')
        Product.objects.all().update(area_code='01-05-03-09')

        self.client.force_authenticate(self.buyer)
        res = self.client.get('/api/ecommerce/feed/?area_code=01-05-03-77')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 1)  # grouped into one card
        card = res.data['results'][0]
        self.assertEqual(card['vendor_count'], 2)
        # 1000 + 10% = 1100 (min);  1200 + 10% = 1320 (max)
        self.assertEqual(card['min_price'], '1100.00')
        self.assertEqual(card['max_price'], '1320.00')

    def test_05_feed_excludes_other_area(self):
        self._build_config()
        self.client.force_authenticate(self.merchant_a)
        self.client.post('/api/ecommerce/products/',
                         self._product_payload(self.biz_a.id, 'NIKE-A', '1200.00'), format='json')
        Product.objects.all().update(area_code='07-01-01-01')
        self.client.force_authenticate(self.buyer)
        res = self.client.get('/api/ecommerce/feed/?area_code=01-05-03-77')
        self.assertEqual(res.data['count'], 0)

    def _place_order(self, price='1200.00'):
        self._build_config()
        self.client.force_authenticate(self.merchant_a)
        prod = self.client.post('/api/ecommerce/products/',
                                self._product_payload(self.biz_a.id, 'NIKE-001', price), format='json')
        variant_id = ProductVariant.objects.get(product_id=prod.data['id']).id

        self.client.force_authenticate(self.buyer)
        self.client.post('/api/ecommerce/cart/', {'variant': variant_id, 'quantity': 1}, format='json')
        cart = Cart.objects.get(user=self.buyer, status=Cart.STATUS_ACTIVE)
        res = self.client.post('/api/ecommerce/orders/place/', {'cart': cart.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        return Order.objects.get(id=res.data['id']), variant_id

    def test_06_place_order_money_breakdown_and_stock(self):
        order, variant_id = self._place_order('1200.00')
        # vendor 1200 + 10% commission 120 = 1320 subtotal; + 40 delivery = 1360 total
        self.assertEqual(order.vendor_subtotal, Decimal('1200.00'))
        self.assertEqual(order.commission_amount, Decimal('120.00'))
        self.assertEqual(order.subtotal, Decimal('1320.00'))
        self.assertEqual(order.delivery_fee, Decimal('40.00'))
        self.assertEqual(order.total_amount, Decimal('1360.00'))
        self.assertEqual(order.status, Order.STATUS_PENDING_ASSIGNMENT)
        self.assertEqual(order.payment_status, Order.PAYMENT_PENDING)
        self.assertEqual(ProductVariant.objects.get(id=variant_id).stock_qty, 9)

    def test_07_admin_routing_accept_flow(self):
        order, _ = self._place_order()
        self.client.force_authenticate(self.admin)
        res = self.client.post(f'/api/ecommerce/admin-orders/{order.id}/assign-vendor/',
                               {'business_family': self.biz_a.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_ASSIGNED)
        self.assertTrue(OrderVendorAssignment.objects.filter(
            order=order, business_family=self.biz_a, status=OrderVendorAssignment.OFFERED).exists())

        self.client.force_authenticate(self.merchant_a)
        res = self.client.post(f'/api/ecommerce/vendor-orders/{order.id}/accept/', {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_ACCEPTED)
        self.assertEqual(order.business_family_id, self.biz_a.id)
        self.assertIsNotNone(order.assigned_at)

    def test_08_admin_routing_reject_then_reroute(self):
        order, _ = self._place_order()
        self.client.force_authenticate(self.admin)
        self.client.post(f'/api/ecommerce/admin-orders/{order.id}/assign-vendor/',
                         {'business_family': self.biz_b.id}, format='json')
        self.client.force_authenticate(self.merchant_b)
        res = self.client.post(f'/api/ecommerce/vendor-orders/{order.id}/reject/',
                               {'note': 'Out of stock'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PENDING_ASSIGNMENT)

        self.client.force_authenticate(self.admin)
        self.client.post(f'/api/ecommerce/admin-orders/{order.id}/assign-vendor/',
                         {'business_family': self.biz_a.id}, format='json')
        self.client.force_authenticate(self.merchant_a)
        self.client.post(f'/api/ecommerce/vendor-orders/{order.id}/accept/', {}, format='json')
        order.refresh_from_db()
        self.assertEqual(order.business_family_id, self.biz_a.id)

    def test_09_delivery_flow_marks_paid(self):
        order, _ = self._place_order()
        self.client.force_authenticate(self.admin)
        self.client.post(f'/api/ecommerce/admin-orders/{order.id}/assign-vendor/',
                         {'business_family': self.biz_a.id}, format='json')
        self.client.force_authenticate(self.merchant_a)
        self.client.post(f'/api/ecommerce/vendor-orders/{order.id}/accept/', {}, format='json')
        self.client.post(f'/api/ecommerce/vendor-orders/{order.id}/assign-agent/',
                         {'agent': self.agent.id}, format='json')
        self.client.post(f'/api/ecommerce/vendor-orders/{order.id}/delivery-status/',
                         {'status': 'picked_up'}, format='json')
        res = self.client.post(f'/api/ecommerce/vendor-orders/{order.id}/delivery-status/',
                               {'status': 'delivered', 'proof_image': _proof_file()}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_DELIVERED)
        self.assertEqual(order.payment_status, Order.PAYMENT_PAID)

    def test_10_cancel_restocks(self):
        order, variant_id = self._place_order()
        self.assertEqual(ProductVariant.objects.get(id=variant_id).stock_qty, 9)
        self.client.force_authenticate(self.buyer)
        res = self.client.post(f'/api/ecommerce/my-orders/{order.id}/cancel/', {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_CANCELLED)
        self.assertEqual(ProductVariant.objects.get(id=variant_id).stock_qty, 10)

    def test_11_stock_adjust_endpoint(self):
        self._build_config()
        self.client.force_authenticate(self.merchant_a)
        prod = self.client.post('/api/ecommerce/products/',
                                self._product_payload(self.biz_a.id, 'NIKE-001', '1200.00'), format='json')
        variant = ProductVariant.objects.get(product_id=prod.data['id'])
        res = self.client.post(f'/api/ecommerce/variants/{variant.id}/stock/',
                               {'movement_type': 'adjustment', 'quantity_delta': 5,
                                'reason': 'Recount'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertEqual(res.data['balance_after'], 15)

    def test_12_non_admin_cannot_manage_config(self):
        self.client.force_authenticate(self.merchant_a)
        res = self.client.post('/api/ecommerce/unit-types/',
                               {'name': 'X', 'code': 'x'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # ---- delivery management -------------------------------------------------------
    def _accept_order(self):
        order, _ = self._place_order()
        self.client.force_authenticate(self.admin)
        self.client.post(f'/api/ecommerce/admin-orders/{order.id}/assign-vendor/',
                         {'business_family': self.biz_a.id}, format='json')
        self.client.force_authenticate(self.merchant_a)
        self.client.post(f'/api/ecommerce/vendor-orders/{order.id}/accept/', {}, format='json')
        return order

    def test_13_assign_agent_must_be_vendor_employee(self):
        order = self._accept_order()
        self.client.force_authenticate(self.merchant_a)
        # merchant_b is NOT an employee of vendor A -> rejected.
        res = self.client.post(f'/api/ecommerce/vendor-orders/{order.id}/assign-agent/',
                               {'agent': self.merchant_b.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        # agent IS an employee of vendor A -> accepted.
        res = self.client.post(f'/api/ecommerce/vendor-orders/{order.id}/assign-agent/',
                               {'agent': self.agent.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)

    def test_14_agent_delivery_flow(self):
        order = self._accept_order()
        self.client.force_authenticate(self.merchant_a)
        self.client.post(f'/api/ecommerce/vendor-orders/{order.id}/assign-agent/',
                         {'agent': self.agent.id}, format='json')

        # Agent sees only their own deliveries.
        self.client.force_authenticate(self.agent)
        res = self.client.get('/api/ecommerce/my-deliveries/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data['results'] if 'results' in res.data else res.data
        self.assertEqual(len(results), 1)
        delivery_id = results[0]['id']

        self.client.post(f'/api/ecommerce/my-deliveries/{delivery_id}/accept/', {}, format='json')
        self.client.post(f'/api/ecommerce/my-deliveries/{delivery_id}/status/',
                         {'status': 'picked_up'}, format='json')

        # Delivered WITHOUT proof is rejected.
        res = self.client.post(f'/api/ecommerce/my-deliveries/{delivery_id}/status/',
                               {'status': 'delivered'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Delivered WITH proof succeeds and marks the order paid.
        res = self.client.post(f'/api/ecommerce/my-deliveries/{delivery_id}/status/',
                               {'status': 'delivered', 'proof_image': _proof_file()}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_DELIVERED)
        self.assertEqual(order.payment_status, Order.PAYMENT_PAID)

    def test_15_agent_cannot_see_others_delivery(self):
        order = self._accept_order()
        self.client.force_authenticate(self.merchant_a)
        self.client.post(f'/api/ecommerce/vendor-orders/{order.id}/assign-agent/',
                         {'agent': self.agent.id}, format='json')
        # A different user (buyer) has no deliveries.
        self.client.force_authenticate(self.buyer)
        res = self.client.get('/api/ecommerce/my-deliveries/')
        results = res.data['results'] if 'results' in res.data else res.data
        self.assertEqual(len(results), 0)
