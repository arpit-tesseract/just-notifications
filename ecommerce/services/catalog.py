"""Catalog helpers: dynamic form schema, grouping key, and area-code resolution."""
from django.conf import settings
from django.utils.text import slugify

# How many leading residential-code segments define an "area" for discovery/routing.
AREA_MATCH_SEGMENTS = getattr(settings, 'ECOMMERCE_AREA_MATCH_SEGMENTS', 3)


def area_prefix(code):
    """Leading area-level prefix of a dash-separated residential code."""
    if not code:
        return None
    return '-'.join(str(code).split('-')[:AREA_MATCH_SEGMENTS])


def resolve_business_area_code(business_family):
    """The merchant's business residential code (reused from residence configuration)."""
    from user.models import ResidentMapping
    rm = (
        ResidentMapping.objects
        .filter(business_family=business_family, residential_details__isnull=False)
        .select_related('residential_details')
        .first()
    )
    if rm and rm.residential_details:
        return rm.residential_details.residential_code
    return None


def build_grouping_key(template_id, name):
    """Groups identical products across vendors for the price-range card."""
    return f"{template_id}:{slugify(name or '')}"


def build_variant_concept_key(template_id, parts):
    """
    Identity of "the same variant across vendors" so the admin can find every vendor who
    stocks it. ``parts`` = iterable of (attribute_code, value, unit_name-or-None) for the
    variant-defining attributes only. Two vendors' Blue / US-8 produce the same key.
    """
    sig = "|".join(sorted(f"{code}={value}@{unit or ''}" for code, value, unit in parts))
    return f"{template_id}::{sig}"


def build_form_schema(template):
    """
    Dynamic form definition for a template. React / React Native render the merchant's
    'add product' form from this JSON.
    """
    fields = []
    template_attrs = (
        template.template_attributes
        .filter(is_deleted=False)
        .select_related('attribute', 'attribute__unit_type', 'default_unit')
        .order_by('sort_order', 'id')
    )
    for ta in template_attrs:
        attr = ta.attribute
        field = {
            'template_attribute_id': ta.id,
            'attribute_id': attr.id,
            'name': attr.name,
            'code': attr.code,
            'input_type': attr.input_type,
            'is_required': ta.is_required,
            'is_variant_defining': ta.is_variant_defining,
            'is_image_defining': ta.is_image_defining,
            'help_text': attr.help_text,
            'default_unit_id': ta.default_unit_id,
            'options': [],
            'units': [],
        }
        if attr.has_options:
            # Options carry their unit (or null = all units). The merchant UI filters the
            # dropdown to the selected unit's options + the all-unit options.
            field['options'] = [
                {
                    'id': o.id,
                    'value': o.value,
                    'display_value': o.display_value or o.value,
                    'color_hex': o.color_hex,
                    'unit_id': o.unit_id,
                }
                for o in attr.options.filter(is_deleted=False, is_active=True).order_by('sort_order', 'id')
            ]
        if attr.unit_type_id:
            field['units'] = [
                {'id': u.id, 'name': u.name, 'symbol': u.symbol}
                for u in attr.unit_type.units.filter(is_deleted=False, is_active=True).order_by('sort_order', 'id')
            ]
        fields.append(field)

    return {
        'template_id': template.id,
        'template_name': template.name,
        'commission_type': template.commission_type,
        'commission_value': str(template.commission_value),
        'fields': fields,
    }
