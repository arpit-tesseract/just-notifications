from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import *
# Register your models here.

@admin.register(WalletType)
class WalletTypeAdmin(SimpleHistoryAdmin):
    list_display = ("name",)
    
    
# @admin.register(LimitType)
# class LimitTypeAdmin(SimpleHistoryAdmin):
#     list_display = ("name",)


@admin.register(WalletTypeLimit)
class WalletTypeLimitAdmin(SimpleHistoryAdmin):
    list_display = ("wallet_type", "entry_type", "limit_amount")


@admin.register(Wallet)
class WalletAdmin(SimpleHistoryAdmin):
    list_display = ("owner_user", "wallet_type", "balance")


@admin.register(WalletLimit)
class WalletLimitAdmin(SimpleHistoryAdmin):
    list_display = ("wallet", "wallet_type_limit", "used_amount", "remaining")
    

@admin.register(WalletMember)
class WalletMemberAdmin(SimpleHistoryAdmin):
    list_display = ("wallet", "user", "can_transfer")


@admin.register(WalletMemberLimit)
class WalletMemberLimitAdmin(SimpleHistoryAdmin):
    list_display = ("wallet_member", "limit_amount", "used_amount")


@admin.register(TransactionCategory)
class TransactionCategoryAdmin(SimpleHistoryAdmin):
    list_display = ("name",)


@admin.register(Transaction)
class TransactionAdmin(SimpleHistoryAdmin):
    list_display = ("sender_wallet_member", "receiver_wallet_member", "amount", "current_status", "time_stamp")

# @admin.register(Transaction)
# class TransactionAdmin(SimpleHistoryAdmin):
#     list_display = ("user", "wallet_member", "amount", "current_status", "time_stamp")    

@admin.register(TransactionStatusLog)
class TransactionStatusLogAdmin(admin.ModelAdmin):
    list_display = ("transaction", "status", "time_stamp", "summary")
    

@admin.register(TransactionType)
class TransactionTypeAdmin(SimpleHistoryAdmin):
    list_display = ("name",)


# @admin.register(TransactionHistory)
# class TransactionHistoryAdmin(SimpleHistoryAdmin):
#     list_display = ("transaction", "transaction_type", "currency", "item", "time_stamp", "summary")
    

@admin.register(WalletLedger)
class WalletLedgerAdmin(SimpleHistoryAdmin):
    list_display = ("wallet", "transaction", "entry_type", "balance_after", "time_stamp")
    
@admin.register(MoneyRequest)
class MoneyRequestAdmin(SimpleHistoryAdmin):
    list_display = ("request_wallet_member", "payer_wallet_member", "amount", "current_status", "time_stamp")

@admin.register(MoneyRequestStatusLog)
class MoneyRequestStatusLogAdmin(admin.ModelAdmin):
    list_display = ("money_request", "status", "time_stamp", "summary")