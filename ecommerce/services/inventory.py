"""Inventory service: apply stock movements atomically and keep balances in sync."""
from django.db import transaction

from ecommerce.models import LowStockAlert, ProductVariant, StockMovement


@transaction.atomic
def apply_movement(variant, movement_type, quantity_delta, *, reason=None,
                   reference_type=None, reference_id=None, user=None):
    """
    Adjust a variant's stock by ``quantity_delta`` (+in / -out), record a StockMovement
    with the resulting balance, and raise a LowStockAlert when it crosses the threshold.
    """
    variant = ProductVariant.all_objects.select_for_update().get(pk=variant.pk)
    new_balance = variant.stock_qty + quantity_delta
    if new_balance < 0:
        raise ValueError(
            f"Insufficient stock for '{variant.sku}': have {variant.stock_qty}, need {-quantity_delta}."
        )

    variant.stock_qty = new_balance
    if new_balance == 0 and variant.status == ProductVariant.STATUS_ACTIVE:
        variant.status = ProductVariant.STATUS_OUT_OF_STOCK
    elif new_balance > 0 and variant.status == ProductVariant.STATUS_OUT_OF_STOCK:
        variant.status = ProductVariant.STATUS_ACTIVE
    variant.save(update_fields=['stock_qty', 'status', 'updated_at'])

    movement = StockMovement.objects.create(
        variant=variant,
        movement_type=movement_type,
        quantity_delta=quantity_delta,
        balance_after=new_balance,
        reason=reason,
        reference_type=reference_type,
        reference_id=reference_id,
        created_by=user,
    )

    if variant.low_stock_threshold and new_balance <= variant.low_stock_threshold:
        LowStockAlert.objects.create(
            variant=variant,
            threshold=variant.low_stock_threshold,
            stock_at_alert=new_balance,
        )

    return movement
