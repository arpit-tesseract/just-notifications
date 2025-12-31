from django.urls import path
from .import views

urlpatterns = [
    path("", views.WalletView.as_view(), name="wallet-type"),
    path("wallet-to-wallet-transfer/", views.WalletToWalletTransfer.as_view(), name="wallet-to-wallet-transfer"),
    path("transaction-categories-lst/", views.TransactionCategoryView.as_view(), name="transaction-category"),
    path("transaction-history/", views.TransactionHistoryView.as_view(), name="transaction-history"),
    path("wallet-history/", views.WalletLedgerView.as_view(), name="wallet-ledger"),
]
