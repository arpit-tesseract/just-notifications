# from django.db import models
# from common.models import Status
# from user_management.models import CustomUser, ProfessionalDetail
# from configuration.models import Item
# from simple_history.models import HistoricalRecords
# from django.utils import timezone
# from django.core.validators import MinValueValidator
# # Create your models here.


# LIMIT_TYPE_CHOICES = (
#         ('PER_TRANSACTION', 'PER_TRANSACTION'),
#         ('DAILY', 'DAILY'),
#         ('WEEKLY', 'WEEKLY'),
#         ('MONTHLY', 'MONTHLY'),
#         ('YEARLY', 'YEARLY'),
#     )

# class WalletType(models.Model):
#     name = models.CharField(max_length=50, unique=True)
#     is_active = models.BooleanField(default=True)
#     time_stamp = models.DateTimeField(auto_now_add=True)
    
#     history = HistoricalRecords()
    
#     def __str__(self):
#         return self.name


# # per transaction, daily, monthly, yearly ect.
# # class LimitType(models.Model):
# #     name = models.CharField(max_length=50, unique=True)
# #     is_active = models.BooleanField(default=True)
# #     time_stamp = models.DateTimeField(auto_now_add=True)
    
# #     history = HistoricalRecords()
    
# #     def __str__(self):
# #         return self.name


# class WalletTypeLimit(models.Model):
#     ENTRY_TYPE_CHOICES = (
#         ('DEBIT', 'DEBIT'),
#         ('CREDIT', 'CREDIT'),
#     )
#     wallet_type = models.ForeignKey(WalletType, on_delete=models.CASCADE, related_name="limits")
#     limit_type = models.CharField(max_length=20, choices=LIMIT_TYPE_CHOICES)
#     entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES)
#     limit_amount = models.DecimalField(max_digits=30, decimal_places=2, default=0)
#     time_stamp = models.DateTimeField(auto_now_add=True)
    
#     history = HistoricalRecords()
    
#     def __str__(self):
#         return f"{self.limit_type} Limit for: {self.wallet_type.name} wallet."


# class Wallet(models.Model):
#     owner_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="wallets_of_users")
#     professional_detail = models.ForeignKey(ProfessionalDetail, on_delete=models.SET_NULL, blank=True, null=True, related_name="wallets_of_professional_detail") 
#     wallet_type = models.ForeignKey(WalletType, on_delete=models.SET_NULL, blank=True, null=True, related_name="wallets_of_wallet_type")
#     status = models.ForeignKey(Status, on_delete=models.SET_NULL, blank=True, null=True)
#     balance = models.DecimalField(max_digits=30, decimal_places=2, default=0)
#     time_stamp = models.DateTimeField(auto_now_add=True)
    
#     history = HistoricalRecords()
    
#     def __str__(self):
#         return f"{self.wallet_type.name} - {self.owner_user}"


# class WalletLimit(models.Model):
#     wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="wallet_limits_of_wallet")
#     wallet_type_limit = models.ForeignKey(WalletTypeLimit, on_delete=models.SET_NULL, blank=True, null=True, related_name="wallet_limits_of_wallet_type_limit")
#     used_amount = models.DecimalField(max_digits=30, decimal_places=2, default=0)
#     reset_at = models.DateTimeField(null=True, blank=True) # daily/monthly reset
#     time_stamp = models.DateTimeField(auto_now_add=True)
    
#     history = HistoricalRecords()
    
#     def remaining(self):
#         return self.wallet_type_limit.limit_amount - self.used_amount
    

# class WalletMember(models.Model):
#     wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="wallet_members_of_wallet")
#     user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="wallet_members_of_user")
#     can_transfer = models.BooleanField(default=True)
#     can_check_balance = models.BooleanField(default=False)
#     # deligated_limit = models.DecimalField(max_digits=30, decimal_places=2, default=0, null=True, blank=True)
#     time_stamp = models.DateTimeField(auto_now_add=True)
    
#     history = HistoricalRecords()
    
#     def __str__(self):
#         return f"{self.wallet.wallet_type.name} - {self.user}"
    
#     def is_wallet_owner(self):
#         if self.user == self.wallet.owner_user:
#             return True
#         else:
#             return False
        
#     def check_can_transfer(self):
#         if self.is_wallet_owner():
#             return True
#         else:
#             if self.can_transfer:
#                 return True
#             else:
#                 return False
    
#     # def check_credit_limit(self):
#     #     receiver_wallet = self.wallet
        
#     #     receiver_wallet_type_limits = WalletLimit.objects.filter(
#     #         wallet=receiver_wallet,
#     #         wallet_type_limit__entry_type="CREDIT"
#     #     )
    


# class WalletMemberLimit(models.Model):
#     wallet_member = models.ForeignKey(WalletMember, on_delete=models.CASCADE, related_name="wallet_member_limits_of_wallet_member")
#     # limit_type = models.CharField(max_length=20, choices=LIMIT_TYPE_CHOICES)
#     limit_amount = models.DecimalField(max_digits=30, decimal_places=2)
#     used_amount = models.DecimalField(max_digits=30, decimal_places=2, default=0)
#     reset_at = models.DateTimeField(null=True, blank=True)  # daily/monthly reset
#     time_stamp = models.DateTimeField(auto_now_add=True)
#     history = HistoricalRecords()

#     def remaining(self):
#         return self.limit_amount - self.used_amount


# class TransactionCategory(models.Model):
#     name = models.CharField(max_length=50, unique=True)
#     is_active = models.BooleanField(default=True)
#     time_stamp = models.DateTimeField(auto_now_add=True)
    
#     history = HistoricalRecords()
    
#     def __str__(self):
#         return self.name

# # cash, wallet_transfer, cheque
# class TransactionType(models.Model):
#     name = models.CharField(max_length=50, unique=True)
#     is_active = models.BooleanField(default=True)
#     time_stamp = models.DateTimeField(auto_now_add=True)
    
#     history = HistoricalRecords()
    
#     def __str__(self):
#         return self.name


# class Transaction(models.Model):
#     CURRENCY_CHOICES = (
#         ('INR', 'INR'),
#         ('USD', 'USD'),
#         ('EUR', 'EUR'),
#     )
#     sender_user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, blank=True, null=True, related_name="transactions_of_sender_user")
#     sender_wallet_member = models.ForeignKey(WalletMember, on_delete=models.SET_NULL, blank=True, null=True, related_name="transactions_of_sender_wallet_member")
#     receiver_wallet_member = models.ForeignKey(WalletMember, on_delete=models.SET_NULL, blank=True, null=True, related_name="transactions_of_receiver_wallet_member")
#     receiver_user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, blank=True, null=True, related_name="transactions_of_receiver_user")
#     reference_id = models.CharField(max_length=255, null=True, blank=True)
#     amount = models.DecimalField(
#         max_digits=15, 
#         decimal_places=2, 
#         validators=[MinValueValidator(0.01)]
#     )
#     summary = models.TextField(null=True, blank=True)
#     transaction_type = models.ForeignKey(TransactionType, on_delete=models.SET_NULL, blank=True, null=True, related_name="transactions_of_transaction_type")
#     file = models.FileField(upload_to="Transaction/Files/", blank=True, null=True)
#     currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, blank=True, null=True)
#     current_status = models.ForeignKey(Status, on_delete=models.SET_NULL, blank=True, null=True)
#     transaction_category = models.ForeignKey(TransactionCategory, on_delete=models.SET_NULL, blank=True, null=True, related_name="transactions_of_transaction_category")
#     time_stamp = models.DateTimeField(auto_now_add=True)
    
#     history = HistoricalRecords()
    
#     def create_status_log(self, model_name, status_name, summary=None):
#         status_obj = Status.get_or_create_status_by_model_name_and_status_name(model_name, status_name)
#         TransactionStatusLog.objects.create(transaction=self, status=status_obj, summary=summary)
#         return status_obj

#     def create_status_log_by_obj(self, status_obj, summary=None):
#         TransactionStatusLog.objects.create(transaction=self, status=status_obj, summary=summary)
#         return status_obj


# class TransactionStatusLog(models.Model):
#     transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="transaction_status_logs_of_transaction")
#     status = models.ForeignKey(Status, on_delete=models.SET_NULL, blank=True, null=True)
#     time_stamp = models.DateTimeField(auto_now_add=True)
#     summary = models.TextField(null=True, blank=True)
    


# class WalletLedger(models.Model):
#     ENTRY_TYPE_CHOICES = (
#         ('DEBIT', 'DEBIT'),
#         ('CREDIT', 'CREDIT'),
#     )
#     wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="wallet_ledgers_of_wallet")
#     transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, blank=True, null=True, related_name="wallet_ledgers_of_transaction")
#     entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES)
#     balance_after = models.DecimalField(max_digits=30, decimal_places=2, default=0)
#     time_stamp = models.DateTimeField(auto_now_add=True)
    
#     history = HistoricalRecords()
    
#     def __str__(self):
#         return f"{self.wallet.wallet_type.name} - {self.wallet.owner_user}"


# class MoneyRequest(models.Model):
#     request_user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, blank=True, null=True, related_name="money_requests_of_request_user")
#     request_wallet_member = models.ForeignKey(WalletMember, on_delete=models.SET_NULL, blank=True, null=True, related_name="money_requests_of_request_wallet_member")
#     payer_user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, blank=True, null=True, related_name="money_requests_of_payer_user")
#     payer_wallet_member = models.ForeignKey(WalletMember, on_delete=models.SET_NULL, blank=True, null=True, related_name="money_requests_of_payer_wallet_member")
#     amount = models.DecimalField(
#         max_digits=30, 
#         decimal_places=2, 
#         validators=[MinValueValidator(0.01)]
#     )
#     summary = models.TextField(null=True, blank=True)
#     current_status = models.ForeignKey(Status, on_delete=models.SET_NULL, blank=True, null=True)
#     transaction = models.OneToOneField(Transaction, on_delete=models.SET_NULL, blank=True, null=True, related_name="money_requests_of_transaction")
#     time_stamp = models.DateTimeField(auto_now_add=True)
    
#     history = HistoricalRecords()
    
#     def create_status_log(self, model_name, status_name, summary=None):
#         status_obj = Status.get_or_create_status_by_model_name_and_status_name(model_name, status_name)
#         MoneyRequestStatusLog.objects.create(money_request=self, status=status_obj, summary=summary)
#         return status_obj
    
#     def create_status_log_by_obj(self, status_obj, summary=None):
#         MoneyRequestStatusLog.objects.create(money_request=self, status=status_obj, summary=summary)
#         return status_obj


# class MoneyRequestStatusLog(models.Model):
#     money_request = models.ForeignKey(MoneyRequest, on_delete=models.CASCADE, related_name="money_request_status_logs_of_money_request")
#     status = models.ForeignKey(Status, on_delete=models.SET_NULL, blank=True, null=True)
#     time_stamp = models.DateTimeField(auto_now_add=True)
#     summary = models.TextField(null=True, blank=True)
    