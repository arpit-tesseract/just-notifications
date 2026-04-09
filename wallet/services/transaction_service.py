# from django.db import transaction
# from decimal import Decimal
# from django.utils import timezone
# from wallet.models import *
# from common.models import Status


# def wallet_transfer(sender_wallet_member, receiver_wallet_member, amount: Decimal):
#     try:
#         with transaction.atomic():
#             if not sender_wallet_member or not receiver_wallet_member:
#                 raise Exception("Transfer not allowed.")
            
#             sender_wallet = sender_wallet_member.wallet
#             receiver_wallet = receiver_wallet_member.wallet
            
#             # Check sender wallet debit limit
#             sender_wallet_type_limits = WalletLimit.objects.filter(
#                 wallet=sender_wallet, 
#                 wallet_type_limit__entry_type="DEBIT"
#             )
#             if sender_wallet_type_limits.exists():
#                 for limit in sender_wallet_type_limits:
#                     if limit.remaining() < amount:
#                         raise Exception(f"{limit.limit_type.name} debit limit exceeded")
            
#             # Check for wallet limits
#             receiver_wallet_type_limits = WalletLimit.objects.filter(
#                 wallet=receiver_wallet,
#                 wallet_type_limit__entry_type="CREDIT"
#             )
#             if receiver_wallet_type_limits.exists():
#                 for limit in receiver_wallet_type_limits:
#                     if limit.remaining() < amount:
#                         raise Exception(f"Receiver has '{limit.limit_type.name}' credit limit exceeded")
                     
#             # Check for wallet balance
#             if sender_wallet.current_balance < amount:
#                 raise Exception("Insufficient balance.")
            
#             # Check for wallet member limits
#             sender_wallet_member_limits = WalletMemberLimit.objects.filter(wallet_member=sender_wallet_member)
#             if sender_wallet_member_limits.exists():
#                 for limit in sender_wallet_member_limits:
#                     if limit.remaining() < amount:
#                         raise Exception(f"{limit.limit_type.name} limit exceeded")
            
#             # Update sender wallet balance
#             sender_wallet.current_balance -= amount
#             sender_wallet.save()
#             WalletLedger.objects.create(wallet=sender_wallet, entry_type="DEBIT", balance_after=sender_wallet.current_balance)
            
#             # Update receiver wallet balance
#             receiver_wallet.current_balance += amount
#             receiver_wallet.save()
#             WalletLedger.objects.create(wallet=receiver_wallet, entry_type="CREDIT", balance_after=receiver_wallet.current_balance)
            
#             # Update sender wallet member limit
#             sender_wallet_member.used_amount += amount
#             sender_wallet_member.save()
            
#             transaction = Transaction.objects.create(sender=sender_wallet_member, receiver=receiver_wallet_member, amount=amount)
#     except Exception as e:
#         pass
                
