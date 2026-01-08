from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Q
from .utils import *
from .serializers import *
from .models import *
# Create your views here.


class WalletToWalletTransfer(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = WalletToWalletTransferSerializer(
            data=request.data,
            context = {'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        sender_wallet_member_obj = serializer.validated_data.get('sender_wallet_member')
        receiver_wallet_member_obj = serializer.validated_data.get('receiver_wallet_member')
        amount = serializer.validated_data.get('amount')
        summary = serializer.validated_data.get('summary')
        
        sender_wallet_id = sender_wallet_member_obj.wallet.id
        receiver_wallet_id = receiver_wallet_member_obj.wallet.id
        
        # transaction_obj = None
        try:
            with transaction.atomic():
                
                # Prevent Deadlocks: Always lock the smaller ID first, then the larger ID.
                # This ensures every transaction acquires locks in the exact same order.
                ids_to_lock = sorted([sender_wallet_id, receiver_wallet_id])

                # Fetch both in one query or sequentially in strictly sorted order
                locked_wallets = {
                    w.id: w for w in Wallet.objects.select_for_update().filter(id__in=ids_to_lock)
                }

                sender_wallet_obj = locked_wallets[sender_wallet_id]
                receiver_wallet_obj = locked_wallets[receiver_wallet_id]
                
                # Re-check balance after locking (Crucial!)
                if sender_wallet_obj.balance < amount:
                    raise serializers.ValidationError("Insufficient balance.")
                
                # create transaction
                transaction_type_obj = get_or_create_transaction_type_obj_by_name("WALLET_TRANSFER")
                transaction_obj = Transaction.objects.create(
                    sender_user = sender_wallet_member_obj.user,
                    sender_wallet_member = sender_wallet_member_obj,
                    receiver_wallet_member = receiver_wallet_member_obj,
                    receiver_user = receiver_wallet_member_obj.user,
                    amount = amount,
                    transaction_type = transaction_type_obj,
                    summary = summary
                )
                
                # create pending status
                status_obj = transaction_obj.create_status_log("Transaction", "INITIATED", summary)
                transaction_obj.current_status = status_obj
                transaction_obj.save()
                
                # decrease sender wallet member debit limit
                decrease_sender_wallet_member_limit(sender_wallet_member_obj.id, amount)
                
                # decrease sender wallet debit limit
                decrease_sender_wallet_debit_limit(sender_wallet_obj, amount)
                
                # decrease receiver wallet credit limit
                decrease_receiver_wallet_credit_limit(receiver_wallet_obj, amount)
                
                # decrease sender wallet balance
                decrease_sender_wallet_balance(sender_wallet_obj, amount)
                
                # increase receiver wallet balance
                increase_receiver_wallet_balance(receiver_wallet_obj, amount)
                
                # create wallet ledger for sender wallet
                WalletLedger.objects.create(
                    wallet = sender_wallet_obj,
                    transaction = transaction_obj,
                    entry_type = "DEBIT",
                    balance_after = sender_wallet_obj.balance,
                )
                
                # create wallet ledger for receiver wallet
                WalletLedger.objects.create(
                    wallet = receiver_wallet_obj,
                    transaction = transaction_obj,
                    entry_type = "CREDIT",
                    balance_after = receiver_wallet_obj.balance,
                )
                
                # Final Success Status
                status_success = transaction_obj.create_status_log("Transaction", "SUCCESS", summary)
                transaction_obj.current_status = status_success
                transaction_obj.save()
            
            # send success response
            return Response({"message": "Transaction successfully completed."}, status=status.HTTP_200_OK)
                    
        except Exception as e:
            # mark_as_failed_transaction(transaction_obj, e)
            return Response(
                {
                    "error": f"Failed to create transaction.",
                    "details": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WalletView(APIView):
    permission_classes = [IsAuthenticated]
    
    def _get_response_data(self, wallet_obj, wallet_member_obj, logged_user):
        balance = None
        limit = None
        
        if wallet_obj.owner_user_id == logged_user.id:
            balance = wallet_obj.balance
        else:
            if wallet_member_obj.can_check_balance:
                balance = wallet_obj.balance
            else:
                balance = None
            # Not owner -> remaining limit
            wallet_limit = wallet_member_obj.wallet_member_limits_of_wallet_member.first()
            limit = wallet_limit.remaining() if wallet_limit else 0

        if wallet_obj.wallet_type.name == "PROFESSIONAL" and wallet_obj.professional_detail:
            company = wallet_obj.professional_detail.brand.name
            return {
                "wallet_member_id": wallet_member_obj.id,
                "wallet_id": wallet_obj.id,
                "wallet_type": wallet_obj.wallet_type.name,
                "company": company,
                "balance": balance,
                "limit": limit
            }
        else:
            return {
                "wallet_member_id": wallet_member_obj.id,
                "wallet_id": wallet_obj.id,
                "wallet_type": wallet_obj.wallet_type.name,
                "balance": balance,
                "limit": limit
            }
    
    def get(self, request):
        logged_user = request.user
    
        str_wallet_id = request.query_params.get('wallet_id', "").strip()
        if str_wallet_id != "":
            wallet_id = int(str_wallet_id)
            wallet_obj = get_object_or_404(Wallet, id=wallet_id)
            
            wallet_member = WalletMember.objects.filter(
                user=logged_user,
                wallet=wallet_obj
            ).first()
                
            if wallet_member:
                output_data = self._get_response_data(wallet_obj, wallet_member, logged_user)
            else:
                return Response({"error": "You do not have access to this wallet."}, status=status.HTTP_403_FORBIDDEN)
                
            return Response(output_data, status=status.HTTP_200_OK)
            
        data = []
        wallet_member_objs = WalletMember.objects.filter(
                user=logged_user
            ).select_related(
                "wallet",
                "wallet__wallet_type",
                "wallet__owner_user"
            ).prefetch_related('wallet_member_limits_of_wallet_member')
        
        for wm in wallet_member_objs:
            wallet_obj = wm.wallet

            output_data = self._get_response_data(wallet_obj, wm, logged_user)
            data.append(output_data)
        return Response(data, status=status.HTTP_200_OK)

class TransactionCategoryView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        transaction_category_objs = TransactionCategory.objects.filter(is_active=True)
        output_data = TransactionCategoryOutputSerializer(transaction_category_objs, many=True).data
        return Response(output_data, status=status.HTTP_200_OK)


class TransactionHistoryView(APIView):
    serializer_class = TransactionHistorySerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = self.request.user
        
        wallet_id = request.query_params.get('wallet_id', None)
        transaction_category_id = request.query_params.get('transaction_category_id', None)
        
        # base filters
        filters = (Q(sender_user=user) | Q(receiver_user=user))
        
        # Filter by transaction category
        if transaction_category_id:
            transaction_category_obj = get_object_or_404(TransactionCategory, id=transaction_category_id)

            filters &= Q(transaction_category=transaction_category_obj)
        
        # Filter by wallet
        if wallet_id is not None:
            wallet_obj = get_object_or_404(Wallet, id=wallet_id)
        
            if not WalletMember.objects.filter(
                wallet_id=wallet_id,
                user=user
            ).exists():
                return Response(
                    {"detail": "You do not have access to this wallet."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            filters &= (
                Q(sender_wallet_member__wallet=wallet_obj) |
                Q(receiver_wallet_member__wallet=wallet_obj)
            )
        
        queryset = (
            Transaction.objects.filter(filters)
            .select_related(
                'transaction_type',
                'transaction_category',
                'current_status',
                'sender_user',
                'receiver_user',
            )
            .order_by('-time_stamp')
        )
            
        output_data = TransactionHistorySerializer(
            queryset,
            many=True,
            context={'request': request}
        ).data
        return Response(output_data, status=status.HTTP_200_OK)


class WalletLedgerView(APIView):
    serializer_class = WalletLedgerSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet_id = request.query_params.get('wallet_id', "").strip()
        if wallet_id == "":
            return Response({"error": "Query paramter 'wallet_id' cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        wallet_obj = get_object_or_404(Wallet, id=wallet_id)
        if request.user != wallet_obj.owner_user:
            return Response({"error": "You do not have access to this wallet."}, status=status.HTTP_403_FORBIDDEN)
        
        wallet_ledger_objs = WalletLedger.objects.filter(wallet=wallet_obj)
        output_data = WalletLedgerSerializer(
            wallet_ledger_objs,
            many = True,
        ).data
        
        return Response(output_data, status=status.HTTP_200_OK)


class GetWalletMemberInfo(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, wallet_member_id):
        try:
            wallet_member_obj = WalletMember.objects.get(id=wallet_member_id)
        except WalletMember.DoesNotExist:
            return Response({"error": "Invalid wallet member id"}, status=status.HTTP_404_NOT_FOUND)
        
        output_data = WalletMemberInfoOutputSerializer(wallet_member_obj).data
        return Response(output_data, status=status.HTTP_200_OK)