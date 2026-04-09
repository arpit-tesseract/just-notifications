# from .models import *


# def get_or_create_transaction_type_obj_by_name(name):
#     transaction_type_obj, created = TransactionType.objects.get_or_create(name=name)
#     return transaction_type_obj
    

# def mark_as_failed_transaction(transaction_obj, e):
#     status_obj = transaction_obj.create_status_log("Transaction", "FAILED", str(e))
#     transaction_obj.current_status = status_obj
#     transaction_obj.save()


# def decrease_sender_wallet_member_limit(sender_wallet_member_id, amount):
#     # Lock the specific limit rows
#     limits = WalletMemberLimit.objects.select_for_update().filter(
#         wallet_member_id=sender_wallet_member_id
#     )
#     # Check Reset Logic here (Pending Logic)
#     for limit in limits:
#         # pending: if limit.reset_at < now(): limit.used_amount = 0
#         limit.used_amount += amount
#         limit.save()


# def decrease_sender_wallet_debit_limit(sender_wallet_locked_obj, amount):
#     # Lock the specific limit rows
#     limits = WalletLimit.objects.select_for_update().filter(
#         wallet=sender_wallet_locked_obj,
#         wallet_type_limit__entry_type="DEBIT"
#     )
#     for limit in limits:
#         limit.used_amount += amount
#         limit.save()


# def decrease_receiver_wallet_credit_limit(receiver_wallet_locked_obj, amount):
#     # Lock the specific limit rows
#     limits = WalletLimit.objects.select_for_update().filter(
#         wallet=receiver_wallet_locked_obj,
#         wallet_type_limit__entry_type="CREDIT"
#     )
#     if limits.exists():
#         for limit in limits:
#             limit.used_amount += amount
#             limit.save()
#             print(f"Decreased receiver wallet credit limit by {amount}")


# def decrease_sender_wallet_balance(sender_wallet_locked_obj, amount):
#     sender_wallet_locked_obj.balance -= amount
#     sender_wallet_locked_obj.save()


# def increase_receiver_wallet_balance(receiver_wallet_locked_obj, amount):
#     receiver_wallet_locked_obj.balance += amount
#     receiver_wallet_locked_obj.save()


