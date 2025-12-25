from django.db import models
from common.models import Status
from user_management.models import CustomUser, ProfessionalDetail
from configuration.models import Item
from simple_history.models import HistoricalRecords
from django.utils import timezone
from django.core.validators import MinValueValidator
# Create your models here.

class WalletType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    time_stamp = models.DateTimeField(auto_now_add=True)
    
    history = HistoricalRecords()
    
    def __str__(self):
        return self.name


# per transaction, daily, monthly, yearly ect.
class LimitType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    time_stamp = models.DateTimeField(auto_now_add=True)
    
    history = HistoricalRecords()
    
    def __str__(self):
        return self.name


class WalletTypeLimit(models.Model):
    ENTRY_TYPE_CHOICES = (
        ('DEBIT', 'DEBIT'),
        ('CREDIT', 'CREDIT'),
    )
    wallet_type = models.ForeignKey(WalletType, on_delete=models.CASCADE)
    LimitType = models.ForeignKey(LimitType, on_delete=models.SET_NULL, blank=True, null=True)
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES)
    limit_amount = models.DecimalField(max_digits=30, decimal_places=2, default=0)
    time_stamp = models.DateTimeField(auto_now_add=True)
    
    history = HistoricalRecords()
    
    def __str__(self):
        return f"Limits for: {self.wallet_type.name} wallet."


class Wallet(models.Model):
    owner_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="wallets")
    professional_detail = models.ForeignKey(ProfessionalDetail, on_delete=models.SET_NULL, blank=True, null=True) 
    wallet_type = models.ForeignKey(WalletType, on_delete=models.SET_NULL, blank=True, null=True)
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, blank=True, null=True)
    balance = models.DecimalField(max_digits=30, decimal_places=2, default=0)
    time_stamp = models.DateTimeField(auto_now_add=True)
    
    history = HistoricalRecords()
    
    def __str__(self):
        return f"{self.wallet_type.name} - {self.owner_user}"


class WalletMember(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    can_transfer = models.BooleanField(default=True)
    deligated_limit = models.DecimalField(max_digits=30, decimal_places=2, default=0, null=True, blank=True)
    time_stamp = models.DateTimeField(auto_now_add=True)
    
    history = HistoricalRecords()
    
    def __str__(self):
        return f"{self.wallet.wallet_type.name} - {self.user}"


class TransactionCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    time_stamp = models.DateTimeField(auto_now_add=True)
    
    history = HistoricalRecords()
    
    def __str__(self):
        return self.name


class Transaction(models.Model):
    sender = models.ForeignKey(WalletMember, on_delete=models.SET_NULL, blank=True, null=True, related_name="sender")
    receiver = models.ForeignKey(WalletMember, on_delete=models.SET_NULL, blank=True, null=True, related_name="receiver")
    reference_id = models.CharField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        validators=[MinValueValidator(0.01)]
    )
    current_status = models.ForeignKey(Status, on_delete=models.SET_NULL, blank=True, null=True)
    transaction_category = models.ForeignKey(TransactionCategory, on_delete=models.SET_NULL, blank=True, null=True)
    time_stamp = models.DateTimeField(auto_now_add=True)


class TransactionStatusLog(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, blank=True, null=True)
    time_stamp = models.DateTimeField(auto_now_add=True)
    summary = models.TextField(null=True, blank=True)
    

# cash, wallet_transfer, cheque
class TransactionType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    time_stamp = models.DateTimeField(auto_now_add=True)
    
    history = HistoricalRecords()
    
    def __str__(self):
        return self.name


class TransactionHistory(models.Model):
    CURRENCY_CHOICES = (
        ('INR', 'INR'),
        ('USD', 'USD'),
        ('EUR', 'EUR'),
    )
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    transaction_type = models.ForeignKey(TransactionType, on_delete=models.SET_NULL, blank=True, null=True)
    file = models.FileField(upload_to="Transaction/Files/", blank=True, null=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, blank=True, null=True)
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, blank=True, null=True)
    time_stamp = models.DateTimeField(auto_now_add=True)
    summary = models.TextField(null=True, blank=True)
    
    history = HistoricalRecords()
    
    def __str__(self):
        return f"{self.transaction} - {self.transaction_type.name}"


class WalletLedger(models.Model):
    ENTRY_TYPE_CHOICES = (
        ('DEBIT', 'DEBIT'),
        ('CREDIT', 'CREDIT'),
    )
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, blank=True, null=True)
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES)
    balance_after = models.DecimalField(max_digits=30, decimal_places=2, default=0)
    time_stamp = models.DateTimeField(auto_now_add=True)
    
    history = HistoricalRecords()
    
    def __str__(self):
        return f"{self.wallet.wallet_type.name} - {self.wallet.owner_user}"