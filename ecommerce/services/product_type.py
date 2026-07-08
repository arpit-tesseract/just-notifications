"""
Single-call "Create Product Type" upsert.

One admin request can create a fresh product template together with fresh unit types, units,
attributes and (unit-scoped) dropdown options -- and/or reuse existing ones by id. Posting a
payload that carries ids updates in place; posting without ids creates. The GET-details
response uses the exact same shape as the POST body, so the client round-trips it.

Payload shape (also what GET returns):
{
  "id": null,                       # template id -> update if present, else create
  "name": "Shoes", "code": "shoes",
  "category": null, "description": "...",
  "commission_type": "percent", "commission_value": "10.00", "is_active": true,
  "attributes": [
    {
      "id": null,                   # attribute id -> reuse/update if present, else create
      "name": "Size", "code": "size", "input_type": "dropdown",   # or "raw_input"
      "unit_type": {                # optional
        "id": null, "name": "Shoe Size System", "code": "shoe_size",
        "units": [ {"id": null, "name": "US", "is_base": true}, {"name": "UK"} ]
      },
      "options": [                  # dropdown values, optionally per unit
        {"id": null, "value": "7", "unit_name": "UK"},
        {"id": null, "value": "8", "unit_name": "US"}
      ],
      "is_required": true, "is_variant_defining": true, "is_image_defining": false,
      "default_unit_name": "US", "sort_order": 1
    }
  ]
}
"""
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils.text import slugify

from ecommerce.models import (
    Attribute, AttributeOption, ProductTemplate, TemplateAttribute, Unit, UnitType,
)

# "Raw Input" in the client UI is stored as a plain text attribute.
INPUT_TYPE_ALIASES = {'raw_input': Attribute.INPUT_TEXT, 'raw': Attribute.INPUT_TEXT}
VALID_INPUT_TYPES = {c[0] for c in Attribute.INPUT_TYPE_CHOICES}


def _decimal(value, default='0'):
    try:
        return Decimal(str(value if value not in (None, '') else default))
    except (InvalidOperation, TypeError):
        raise ValueError(f"Invalid decimal value: {value!r}")


def _require(data, field, ctx):
    value = data.get(field)
    if value in (None, ''):
        raise ValueError(f"'{field}' is required for {ctx}.")
    return value


def _resolve_unit_type(utdef):
    """Create/reuse a unit type and its units; return (unit_type, {name: Unit})."""
    if not utdef:
        return None, {}
    ut = None
    if utdef.get('id'):
        ut = UnitType.objects.filter(pk=utdef['id']).first()
        if not ut:
            raise ValueError(f"UnitType id {utdef['id']} not found.")
    if not ut and utdef.get('code'):
        ut = UnitType.objects.filter(code=utdef['code'], is_deleted=False).first()
    if ut:
        ut.name = utdef.get('name', ut.name)
        ut.save(update_fields=['name', 'updated_at'])
    else:
        name = _require(utdef, 'name', 'unit_type')
        code = utdef.get('code') or slugify(name)
        ut = UnitType.objects.create(name=name, code=code)

    for udef in utdef.get('units', []) or []:
        unit = None
        if udef.get('id'):
            unit = Unit.objects.filter(pk=udef['id']).first()
        if not unit:
            unit = Unit.objects.filter(unit_type=ut, name=udef.get('name'), is_deleted=False).first()
        fields = dict(
            name=_require(udef, 'name', 'unit'),
            symbol=udef.get('symbol'),
            is_base=udef.get('is_base', False),
            sort_order=udef.get('sort_order', 1),
        )
        if unit:
            for k, v in fields.items():
                setattr(unit, k, v)
            unit.save()
        else:
            Unit.objects.create(unit_type=ut, **fields)

    unit_map = {u.name: u for u in ut.units.filter(is_deleted=False)}
    return ut, unit_map


def _resolve_attribute(adef, unit_type):
    input_type = (adef.get('input_type') or Attribute.INPUT_TEXT).lower()
    input_type = INPUT_TYPE_ALIASES.get(input_type, input_type)
    if input_type not in VALID_INPUT_TYPES:
        raise ValueError(f"Invalid input_type '{adef.get('input_type')}'.")

    attribute = None
    if adef.get('id'):
        attribute = Attribute.objects.filter(pk=adef['id']).first()
        if not attribute:
            raise ValueError(f"Attribute id {adef['id']} not found.")
    if not attribute and adef.get('code'):
        attribute = Attribute.objects.filter(code=adef['code'], is_deleted=False).first()

    name = adef.get('name') or (attribute.name if attribute else None)
    _require({'name': name}, 'name', 'attribute')
    code = adef.get('code') or (attribute.code if attribute else slugify(name))
    fields = dict(name=name, code=code, input_type=input_type, unit_type=unit_type,
                  help_text=adef.get('help_text'))
    if attribute:
        for k, v in fields.items():
            setattr(attribute, k, v)
        attribute.save()
    else:
        attribute = Attribute.objects.create(**fields)
    return attribute


def _sync_options(attribute, options, unit_map):
    for odef in options or []:
        unit = unit_map.get(odef.get('unit_name')) if odef.get('unit_name') else None
        value = _require(odef, 'value', 'option')
        defaults = dict(
            display_value=odef.get('display_value') or value,
            color_hex=odef.get('color_hex'),
            sort_order=odef.get('sort_order', 1),
            is_active=odef.get('is_active', True),
        )
        option = None
        if odef.get('id'):
            option = AttributeOption.objects.filter(pk=odef['id']).first()
        if not option:
            option = AttributeOption.objects.filter(
                attribute=attribute, unit=unit, value=value, is_deleted=False).first()
        if option:
            for k, v in defaults.items():
                setattr(option, k, v)
            option.save()
        else:
            AttributeOption.objects.create(attribute=attribute, unit=unit, value=value, **defaults)


@transaction.atomic
def upsert_product_type(data, user=None):
    tfields = dict(
        name=_require(data, 'name', 'product type'),
        code=data.get('code') or slugify(data['name']),
        category_id=data.get('category'),
        description=data.get('description'),
        commission_type=data.get('commission_type', ProductTemplate.COMMISSION_PERCENT),
        commission_value=_decimal(data.get('commission_value'), '0'),
        is_active=data.get('is_active', True),
    )
    template = None
    if data.get('id'):
        template = ProductTemplate.objects.filter(pk=data['id']).first()
        if not template:
            raise ValueError(f"ProductTemplate id {data['id']} not found.")
    if not template:
        template = ProductTemplate.objects.filter(code=tfields['code'], is_deleted=False).first()
    if template:
        for k, v in tfields.items():
            setattr(template, k, v)
        template.save()
    else:
        template = ProductTemplate.objects.create(**tfields)

    for order, adef in enumerate(data.get('attributes', []) or [], start=1):
        unit_type, unit_map = _resolve_unit_type(adef.get('unit_type'))
        attribute = _resolve_attribute(adef, unit_type)
        if attribute.has_options:
            _sync_options(attribute, adef.get('options'), unit_map)

        default_unit = unit_map.get(adef.get('default_unit_name')) if adef.get('default_unit_name') else None
        ta, _ = TemplateAttribute.objects.get_or_create(template=template, attribute=attribute)
        ta.is_required = adef.get('is_required', False)
        ta.is_variant_defining = adef.get('is_variant_defining', False)
        ta.is_image_defining = adef.get('is_image_defining', False)
        ta.default_unit = default_unit
        ta.sort_order = adef.get('sort_order', order)
        ta.save()

    return template


def serialize_product_type(template):
    """Full nested detail -- the same shape the upsert POST accepts."""
    attributes = []
    links = (
        template.template_attributes.filter(is_deleted=False)
        .select_related('attribute', 'attribute__unit_type', 'default_unit')
        .order_by('sort_order', 'id')
    )
    for ta in links:
        attr = ta.attribute
        unit_type = None
        if attr.unit_type_id:
            ut = attr.unit_type
            unit_type = {
                'id': ut.id, 'name': ut.name, 'code': ut.code,
                'units': [
                    {'id': u.id, 'name': u.name, 'symbol': u.symbol, 'is_base': u.is_base,
                     'sort_order': u.sort_order}
                    for u in ut.units.filter(is_deleted=False).order_by('sort_order', 'id')
                ],
            }
        options = [
            {'id': o.id, 'value': o.value, 'display_value': o.display_value or o.value,
             'unit_name': o.unit.name if o.unit_id else None, 'color_hex': o.color_hex,
             'sort_order': o.sort_order}
            for o in attr.options.filter(is_deleted=False).order_by('sort_order', 'id')
        ]
        attributes.append({
            'template_attribute_id': ta.id,
            'id': attr.id, 'name': attr.name, 'code': attr.code, 'input_type': attr.input_type,
            'help_text': attr.help_text, 'unit_type': unit_type, 'options': options,
            'is_required': ta.is_required, 'is_variant_defining': ta.is_variant_defining,
            'is_image_defining': ta.is_image_defining,
            'default_unit_name': ta.default_unit.name if ta.default_unit_id else None,
            'sort_order': ta.sort_order,
        })
    return {
        'id': template.id, 'name': template.name, 'code': template.code,
        'category': template.category_id, 'description': template.description,
        'commission_type': template.commission_type,
        'commission_value': str(template.commission_value),
        'is_active': template.is_active, 'attributes': attributes,
    }
