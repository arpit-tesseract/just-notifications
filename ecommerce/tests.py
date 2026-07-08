"""
End-to-end tests for the e-commerce module.

Covers: admin config + dynamic form-schema (unit-scoped dropdown values), merchant nested
product/variant creation (with concept_key), area-based vendor-hidden feed with price range,
cart -> place order as a PRICE RANGE (no stock touched), admin candidate-vendors +
finalize-price-on-assignment (+ stock reserved), accept/reject re-route, status-based
delivery with mandatory proof, and cancellation restock.
"""
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from ecommerce.models import (
    AttributeOption, Cart, Order, Product, ProductVariant, StockMovement, TemplateAttribute,
)
from user.models import BusinessFamily, BusinessFamilyMember, DesignationType, User


def _proof_file():
    return SimpleUploadedFile('proof.jpg', b'proof-bytes', content_type='image/jpeg')


def make_user(contact_no, name, **extra):
    return User.objects.create_user(contact_no=contact_no, password='pass1234', full_name=name, **extra)


def make_business(name, contact_no, email, priority=0):
    return BusinessFamily.objects.create(
        name=name, contact_no=contact_no, email=email, business_type='private_limited',
        priority_score=priority)


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
        cls.biz_a = make_business('Shoe Store A', '+919111111111', 'a@shop.com', priority=10)
        cls.biz_b = make_business('Shoe Store B', '+919222222222', 'b@shop.com', priority=5)
        BusinessFamilyMember.objects.create(
            business_family=cls.biz_a, user=cls.merchant_a, self_designation_type=cls.designation)
        BusinessFamilyMember.objects.create(
            business_family=cls.biz_b, user=cls.merchant_b, self_designation_type=cls.designation)
        BusinessFamilyMember.objects.create(
            business_family=cls.biz_a, user=cls.agent, self_designation_type=cls.designation)

    # ---- helpers -------------------------------------------------------------------
    def _build_config(self):
        self.client.force_authenticate(self.admin)
        ut = self.client.post('/api/ecommerce/unit-types/',
                              {'name': 'Shoe Size System', 'code': 'shoe_size'}, format='json')
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
        self.opt8_id = AttributeOption.objects.get(
            attribute_id=self.size_attr_id, value='8', unit__isnull=True).id

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
        self.template_id = template.data['id']
        tas = TemplateAttribute.objects.filter(template_id=self.template_id)
        self.ta_color = tas.get(attribute_id=self.color_attr_id)
        self.ta_size = tas.get(attribute_id=self.size_attr_id)

    def _product_payload(self, business_id, sku, price):
        return {
            'business_family': business_id, 'template': self.template_id,
            'name': 'Nike Air', 'sku': sku, 'base_price': '1000.00', 'tax_rate': '0',
            'delivery_fee': '40.00', 'delivery_time_minutes': 45,
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

    def _create_product(self, merchant, business, sku, price):
        self.client.force_authenticate(merchant)
        res = self.client.post('/api/ecommerce/products/',
                               self._product_payload(business.id, sku, price), format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        return ProductVariant.objects.get(product_id=res.data['id'])

    def _place_order(self):
        """Config + two vendors (A@1200, B@1000) + buyer places order from A's variant."""
        self._build_config()
        va = self._create_product(self.merchant_a, self.biz_a, 'NIKE-A', '1200.00')
        self._create_product(self.merchant_b, self.biz_b, 'NIKE-B', '1000.00')
        self.client.force_authenticate(self.buyer)
        self.client.post('/api/ecommerce/cart/', {'variant': va.id, 'quantity': 1}, format='json')
        cart = Cart.objects.get(user=self.buyer, status=Cart.STATUS_ACTIVE)
        res = self.client.post('/api/ecommerce/orders/place/', {'cart': cart.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        return Order.objects.get(id=res.data['id']), cart

    def _accept_order(self, order):
        self.client.force_authenticate(self.admin)
        self.client.post(f'/api/ecommerce/admin-orders/{order.id}/assign-vendor/',
                         {'business_family': self.biz_a.id}, format='json')
        self.client.force_authenticate(self.merchant_a)
        self.client.post(f'/api/ecommerce/vendor-orders/{order.id}/accept/', {}, format='json')
        order.refresh_from_db()

    # ---- config + catalog ----------------------------------------------------------
    def test_01_form_schema_options_carry_unit(self):
        self._build_config()
        res = self.client.get(f'/api/ecommerce/templates/{self.template_id}/form-schema/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        fields = {f['name']: f for f in res.data['fields']}
        self.assertEqual(len(fields['Size']['options']), 3)
        self.assertEqual(len(fields['Size']['units']), 2)
        self.assertIn('unit_id', fields['Size']['options'][0])
        self.assertTrue(fields['Color']['is_image_defining'])

    def test_02_unit_scoped_dropdown_values(self):
        self._build_config()
        # A UK-only size value alongside the all-unit values.
        res = self.client.post('/api/ecommerce/attribute-options/', {
            'attribute': self.size_attr_id, 'unit': self.us_id, 'value': '11', 'sort_order': 9,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        schema = self.client.get(f'/api/ecommerce/templates/{self.template_id}/form-schema/')
        size = next(f for f in schema.data['fields'] if f['name'] == 'Size')
        unit_scoped = [o for o in size['options'] if o['unit_id'] == self.us_id]
        self.assertEqual(len(unit_scoped), 1)
        self.assertEqual(unit_scoped[0]['value'], '11')

    def test_03_product_create_sets_concept_key(self):
        self._build_config()
        variant = self._create_product(self.merchant_a, self.biz_a, 'NIKE-001', '1200.00')
        self.assertTrue(variant.concept_key)
        self.assertEqual(variant.stock_qty, 10)
        self.assertTrue(StockMovement.objects.filter(
            variant=variant, movement_type=StockMovement.PURCHASE).exists())

    def test_04_two_vendors_share_concept_key(self):
        self._build_config()
        va = self._create_product(self.merchant_a, self.biz_a, 'NIKE-A', '1200.00')
        vb = self._create_product(self.merchant_b, self.biz_b, 'NIKE-B', '1000.00')
        self.assertEqual(va.concept_key, vb.concept_key)

    def test_05_merchant_cannot_create_for_others_business(self):
        self._build_config()
        self.client.force_authenticate(self.merchant_a)
        res = self.client.post('/api/ecommerce/products/',
                               self._product_payload(self.biz_b.id, 'X-1', '1200.00'), format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_06_feed_price_range(self):
        self._build_config()
        self._create_product(self.merchant_a, self.biz_a, 'NIKE-A', '1200.00')
        self._create_product(self.merchant_b, self.biz_b, 'NIKE-B', '1000.00')
        Product.objects.all().update(area_code='01-05-03-09')
        self.client.force_authenticate(self.buyer)
        res = self.client.get('/api/ecommerce/feed/?area_code=01-05-03-77')
        self.assertEqual(res.data['count'], 1)
        card = res.data['results'][0]
        self.assertEqual(card['vendor_count'], 2)
        self.assertEqual(card['min_price'], '1100.00')  # 1000 + 10%
        self.assertEqual(card['max_price'], '1320.00')  # 1200 + 10%

    # ---- placement as a price range ------------------------------------------------
    def test_07_place_order_is_a_price_range_no_stock_touched(self):
        order, _ = self._place_order()
        self.assertEqual(order.status, Order.STATUS_PENDING_ASSIGNMENT)
        self.assertFalse(order.is_price_final)
        self.assertEqual(order.estimated_min_total, Decimal('1100.00'))
        self.assertEqual(order.estimated_max_total, Decimal('1320.00'))
        self.assertEqual(order.total_amount, Decimal('0'))
        # No stock touched at placement.
        for v in ProductVariant.objects.all():
            self.assertEqual(v.stock_qty, 10)

    def test_08_cart_cannot_be_reused(self):
        order, cart = self._place_order()
        self.client.force_authenticate(self.buyer)
        res = self.client.post('/api/ecommerce/orders/place/', {'cart': cart.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_09_candidate_vendors_lists_both_with_attributes(self):
        order, _ = self._place_order()
        self.client.force_authenticate(self.admin)
        res = self.client.get(f'/api/ecommerce/admin-orders/{order.id}/candidate-vendors/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        top = res.data[0]  # sorted by priority desc -> Store A (priority 10) first
        self.assertEqual(top['business_family_id'], self.biz_a.id)
        self.assertEqual(top['delivery_time_minutes'], 45)
        self.assertEqual(top['final_total'], '1360.00')  # 1200 + 120 + 40 delivery
        self.assertTrue(top['in_stock'])

    def test_10_assign_finalizes_price_and_reserves_stock(self):
        order, _ = self._place_order()
        va = ProductVariant.objects.get(product__business_family=self.biz_a)
        self.client.force_authenticate(self.admin)
        res = self.client.post(f'/api/ecommerce/admin-orders/{order.id}/assign-vendor/',
                               {'business_family': self.biz_a.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        order.refresh_from_db()
        va.refresh_from_db()
        self.assertTrue(order.is_price_final)
        self.assertEqual(order.status, Order.STATUS_ASSIGNED)
        self.assertEqual(order.business_family_id, self.biz_a.id)
        self.assertEqual(order.total_amount, Decimal('1360.00'))
        self.assertEqual(order.commission_amount, Decimal('120.00'))
        self.assertEqual(va.stock_qty, 9)  # reserved

    def test_11_assign_without_stock_is_rejected(self):
        order, _ = self._place_order()
        ProductVariant.objects.filter(product__business_family=self.biz_a).update(stock_qty=0)
        self.client.force_authenticate(self.admin)
        res = self.client.post(f'/api/ecommerce/admin-orders/{order.id}/assign-vendor/',
                               {'business_family': self.biz_a.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_12_reject_restocks_and_reroutes(self):
        order, _ = self._place_order()
        vb = ProductVariant.objects.get(product__business_family=self.biz_b)
        self.client.force_authenticate(self.admin)
        self.client.post(f'/api/ecommerce/admin-orders/{order.id}/assign-vendor/',
                         {'business_family': self.biz_b.id}, format='json')
        vb.refresh_from_db()
        self.assertEqual(vb.stock_qty, 9)  # reserved on assign
        self.client.force_authenticate(self.merchant_b)
        self.client.post(f'/api/ecommerce/vendor-orders/{order.id}/reject/',
                         {'note': 'nope'}, format='json')
        order.refresh_from_db()
        vb.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PENDING_ASSIGNMENT)
        self.assertFalse(order.is_price_final)
        self.assertEqual(vb.stock_qty, 10)  # restocked
        # Re-route to A and accept.
        self._accept_order(order)
        self.assertEqual(order.business_family_id, self.biz_a.id)

    def test_13_accept_flow(self):
        order, _ = self._place_order()
        self._accept_order(order)
        self.assertEqual(order.status, Order.STATUS_ACCEPTED)
        self.assertEqual(order.business_family_id, self.biz_a.id)
        self.assertIsNotNone(order.assigned_at)

    # ---- delivery ------------------------------------------------------------------
    def test_14_assign_agent_must_be_vendor_employee(self):
        order, _ = self._place_order()
        self._accept_order(order)
        self.client.force_authenticate(self.merchant_a)
        bad = self.client.post(f'/api/ecommerce/vendor-orders/{order.id}/assign-agent/',
                               {'agent': self.merchant_b.id}, format='json')
        self.assertEqual(bad.status_code, status.HTTP_400_BAD_REQUEST)
        ok = self.client.post(f'/api/ecommerce/vendor-orders/{order.id}/assign-agent/',
                              {'agent': self.agent.id}, format='json')
        self.assertEqual(ok.status_code, status.HTTP_200_OK, ok.data)

    def test_15_agent_delivery_requires_proof(self):
        order, _ = self._place_order()
        self._accept_order(order)
        self.client.force_authenticate(self.merchant_a)
        self.client.post(f'/api/ecommerce/vendor-orders/{order.id}/assign-agent/',
                         {'agent': self.agent.id}, format='json')
        self.client.force_authenticate(self.agent)
        d = self.client.get('/api/ecommerce/my-deliveries/')
        results = d.data['results'] if 'results' in d.data else d.data
        delivery_id = results[0]['id']
        self.client.post(f'/api/ecommerce/my-deliveries/{delivery_id}/status/',
                         {'status': 'picked_up'}, format='json')
        no_proof = self.client.post(f'/api/ecommerce/my-deliveries/{delivery_id}/status/',
                                    {'status': 'delivered'}, format='json')
        self.assertEqual(no_proof.status_code, status.HTTP_400_BAD_REQUEST)
        ok = self.client.post(f'/api/ecommerce/my-deliveries/{delivery_id}/status/',
                              {'status': 'delivered', 'proof_image': _proof_file()}, format='multipart')
        self.assertEqual(ok.status_code, status.HTTP_200_OK, ok.data)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_DELIVERED)
        self.assertEqual(order.payment_status, Order.PAYMENT_PAID)

    # ---- cancellation --------------------------------------------------------------
    def test_16_cancel_before_assign_no_restock(self):
        order, _ = self._place_order()
        self.client.force_authenticate(self.buyer)
        res = self.client.post(f'/api/ecommerce/my-orders/{order.id}/cancel/', {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_CANCELLED)
        for v in ProductVariant.objects.all():
            self.assertEqual(v.stock_qty, 10)

    def test_17_cancel_after_assign_restocks(self):
        order, _ = self._place_order()
        self.client.force_authenticate(self.admin)
        self.client.post(f'/api/ecommerce/admin-orders/{order.id}/assign-vendor/',
                         {'business_family': self.biz_a.id}, format='json')
        va = ProductVariant.objects.get(product__business_family=self.biz_a)
        va.refresh_from_db()
        self.assertEqual(va.stock_qty, 9)
        self.client.force_authenticate(self.buyer)
        self.client.post(f'/api/ecommerce/my-orders/{order.id}/cancel/', {}, format='json')
        va.refresh_from_db()
        self.assertEqual(va.stock_qty, 10)

    def test_18_non_admin_cannot_manage_config(self):
        self.client.force_authenticate(self.merchant_a)
        res = self.client.post('/api/ecommerce/unit-types/', {'name': 'X', 'code': 'x'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # ---- single-call product-type upsert -------------------------------------------
    def _perfume_payload(self, **overrides):
        payload = {
            'name': 'Perfume', 'code': 'perfume',
            'commission_type': 'flat', 'commission_value': '25.00',
            'attributes': [
                {
                    'name': 'Quantity', 'code': 'quantity', 'input_type': 'dropdown',
                    'unit_type': {'name': 'Volume', 'code': 'volume',
                                  'units': [{'name': 'ml', 'is_base': True}, {'name': 'L'}]},
                    'options': [{'value': '50', 'unit_name': 'ml'},
                                {'value': '100', 'unit_name': 'ml'},
                                {'value': '1', 'unit_name': 'L'}],
                    'is_required': True, 'is_variant_defining': True,
                    'default_unit_name': 'ml', 'sort_order': 1,
                },
                {'name': 'Fragrance', 'code': 'fragrance', 'input_type': 'raw_input',
                 'is_required': True, 'sort_order': 2},
            ],
        }
        payload.update(overrides)
        return payload

    def test_19_product_type_single_call_creates_everything(self):
        from ecommerce.models import Attribute, ProductTemplate, TemplateAttribute, Unit, UnitType
        self.client.force_authenticate(self.admin)
        res = self.client.post('/api/ecommerce/product-types/', self._perfume_payload(), format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        tid = res.data['id']
        self.assertTrue(ProductTemplate.objects.filter(code='perfume').exists())
        self.assertEqual(UnitType.objects.filter(code='volume').count(), 1)
        self.assertEqual(Unit.objects.filter(unit_type__code='volume').count(), 2)
        self.assertEqual(Attribute.objects.get(code='fragrance').input_type, 'text')  # raw_input -> text
        self.assertEqual(TemplateAttribute.objects.filter(template_id=tid, is_deleted=False).count(), 2)
        # Detail round-trips the same shape.
        detail = self.client.get(f'/api/ecommerce/product-types/{tid}/')
        qty = next(a for a in detail.data['attributes'] if a['code'] == 'quantity')
        self.assertEqual(len(qty['unit_type']['units']), 2)
        self.assertEqual(len(qty['options']), 3)
        self.assertEqual(qty['default_unit_name'], 'ml')

    def test_20_product_type_upsert_updates_by_id(self):
        from ecommerce.models import ProductTemplate
        self.client.force_authenticate(self.admin)
        first = self.client.post('/api/ecommerce/product-types/', self._perfume_payload(), format='json')
        tid = first.data['id']
        again = self.client.post('/api/ecommerce/product-types/',
                                 self._perfume_payload(id=tid, commission_value='30.00'), format='json')
        self.assertEqual(again.status_code, status.HTTP_200_OK, again.data)
        self.assertEqual(ProductTemplate.objects.filter(code='perfume').count(), 1)  # not duplicated
        self.assertEqual(str(ProductTemplate.objects.get(id=tid).commission_value), '30.00')

    def test_21_product_type_reuses_existing_attribute(self):
        from ecommerce.models import Attribute
        self.client.force_authenticate(self.admin)
        color = self.client.post('/api/ecommerce/attributes/',
                                 {'name': 'Color', 'code': 'color', 'input_type': 'text'}, format='json')
        res = self.client.post('/api/ecommerce/product-types/', {
            'name': 'Tee', 'code': 'tee',
            'attributes': [{'id': color.data['id'], 'is_required': True,
                            'is_variant_defining': True, 'sort_order': 1}],
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertEqual(Attribute.objects.filter(code='color').count(), 1)  # reused, not duplicated

    # ---- universal conventions -----------------------------------------------------
    def test_22_dropdown_is_searchable_and_chunked(self):
        self.client.force_authenticate(self.admin)
        for i in range(12):
            self.client.post('/api/ecommerce/unit-types/',
                             {'name': f'Type {i:02d}', 'code': f'type_{i:02d}'}, format='json')
        res = self.client.get('/api/ecommerce/unit-types/dropdown/')
        self.assertEqual(res.data['count'], 12)
        self.assertEqual(len(res.data['results']), 10)  # 10-per-chunk
        filtered = self.client.get('/api/ecommerce/unit-types/dropdown/?search=Type 05')
        self.assertEqual(filtered.data['count'], 1)
        self.assertEqual(filtered.data['results'][0]['name'], 'Type 05')

    def test_23_template_list_is_lightweight_and_searchable(self):
        self._build_config()
        res = self.client.get('/api/ecommerce/templates/?search=Shoes')
        self.assertEqual(res.data['count'], 1)
        row = res.data['results'][0]
        self.assertIn('attribute_count', row)
        self.assertNotIn('template_attributes', row)  # heavy field excluded from list

    def test_24_unique_constraint_messages(self):
        self.client.force_authenticate(self.admin)
        ut = self.client.post('/api/ecommerce/unit-types/',
                              {'name': 'Weight', 'code': 'weight'}, format='json')
        self.client.post('/api/ecommerce/units/',
                         {'unit_type': ut.data['id'], 'name': 'kg'}, format='json')
        dup = self.client.post('/api/ecommerce/units/',
                               {'unit_type': ut.data['id'], 'name': 'kg'}, format='json')
        self.assertEqual(dup.status_code, status.HTTP_400_BAD_REQUEST)

    def test_25_product_sku_unique_message(self):
        self._build_config()
        self._create_product(self.merchant_a, self.biz_a, 'DUP-1', '100.00')
        self.client.force_authenticate(self.merchant_a)
        res = self.client.post('/api/ecommerce/products/',
                               self._product_payload(self.biz_a.id, 'DUP-1', '100.00'), format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('sku', res.data)

    # ---- per-operation serializers -------------------------------------------------
    def test_26_list_and_detail_use_different_serializers(self):
        self._build_config()  # creates a unit type + US/UK units
        self.client.force_authenticate(self.admin)
        listed = self.client.get('/api/ecommerce/units/')
        row = listed.data['results'][0]
        self.assertNotIn('conversion_factor', row)   # lightweight list serializer
        self.assertIn('is_base', row)
        detail = self.client.get(f'/api/ecommerce/units/{row["id"]}/')
        self.assertIn('conversion_factor', detail.data)  # full detail serializer

    def test_27_product_update_uses_scalar_serializer(self):
        self._build_config()
        variant = self._create_product(self.merchant_a, self.biz_a, 'UPD-1', '100.00')
        self.client.force_authenticate(self.merchant_a)
        # PATCH does not require the nested variant_groups payload.
        res = self.client.patch(f'/api/ecommerce/products/{variant.product_id}/',
                                {'name': 'Renamed', 'delivery_time_minutes': 90}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        variant.product.refresh_from_db()
        self.assertEqual(variant.product.name, 'Renamed')
        self.assertEqual(variant.product.delivery_time_minutes, 90)

    def test_28_review_list_is_lightweight_and_filterable(self):
        self._build_config()
        variant = self._create_product(self.merchant_a, self.biz_a, 'REV-1', '100.00')
        self.client.force_authenticate(self.buyer)
        created = self.client.post('/api/ecommerce/reviews/', {
            'product': variant.product_id, 'rating': 5, 'title': 'Nice', 'comment': 'Loved it'},
            format='json')
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        listed = self.client.get(f'/api/ecommerce/reviews/?product={variant.product_id}')
        row = listed.data['results'][0]
        self.assertNotIn('comment', row)   # list serializer omits the heavy field
        self.assertIn('user_name', row)

    def test_29_store_settings_scoped_to_merchant(self):
        # Merchant A creates their store setting; Merchant B can't see it in their list.
        self.client.force_authenticate(self.merchant_a)
        res = self.client.post('/api/ecommerce/store-settings/',
                               {'business_family': self.biz_a.id, 'default_delivery_time_minutes': 30},
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.client.force_authenticate(self.merchant_b)
        listed = self.client.get('/api/ecommerce/store-settings/')
        results = listed.data['results'] if 'results' in listed.data else listed.data
        self.assertEqual(len(results), 0)
