from rest_framework import serializers
from .models import *

class WalletIdNameSerializer(serializers.ModelSerializer):
    wallet_type = serializers.SerializerMethodField()
    class Meta:
        model = Wallet
        fields = ['id', 'wallet_type']
    
    def get_wallet_type(self, obj):
        return obj.wallet_type.name


class WalletInfoSerializer(serializers.Serializer):
    wallet_id = serializers.IntegerField()
    wallet_type = serializers.CharField()
    balance = serializers.DecimalField(max_digits=30, decimal_places=2)

    def get(self, request, wallet_objs):
        logged_user = request.user
        for wallet_obj in wallet_objs:
            if wallet_obj.owner_user == logged_user:
                data = {
                    "wallet_id": wallet_obj.id,
                    "wallet_type": wallet_obj.wallet_type.name,
                    "balance": wallet_obj.balance
                }
                return data
            else:
                wallet_member = WalletMember.objects.filter(
                    user=logged_user,
                    wallet=wallet_obj
                ).first()

                if wallet_member:
                    wallet_limit = WalletMemberLimit.objects.filter(
                        wallet_member=wallet_member
                    ).first()

                    remaining_amount = wallet_limit.remaining() if wallet_limit else 0

                    data = {
                        "wallet_id": wallet_obj.id,
                        "wallet_type": wallet_obj.wallet_type.name,
                        "balance": remaining_amount
                    }
                    return data
                


class TransactionTypeIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionType
        fields = ['id', 'name']

class TransactionCategoryOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionCategory
        fields = ['id', 'name']

class WalletToWalletTransferSerializer(serializers.Serializer):
    sender_wallet_member = serializers.PrimaryKeyRelatedField(queryset=WalletMember.objects.all())
    receiver_wallet_member = serializers.PrimaryKeyRelatedField(queryset=WalletMember.objects.all())
    amount = serializers.DecimalField(max_digits=30, decimal_places=2)
    summary = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs, *args, **kwargs):
        super().validate(attrs)
        
        sender_wallet_member = attrs['sender_wallet_member']
        receiver_wallet_member = attrs['receiver_wallet_member']
        amount = attrs['amount']
        
        if sender_wallet_member.id == receiver_wallet_member.id:
            raise serializers.ValidationError({"receiver_wallet_member": "You cannot transfer to yourself."})
        
        # Check amount
        if amount.as_tuple().exponent < -2:
            raise serializers.ValidationError("Amount supports max 2 decimal places.")
        
        if amount <= 0:
            raise serializers.ValidationError({"amount": "Amount must be greater than 0."})
        
        
        request = self.context.get('request')
        logged_user = request.user
        if logged_user != sender_wallet_member.user:
            raise serializers.ValidationError({"sender_wallet_member": "Invalid sender wallet member."})
        
        sender_wallet = sender_wallet_member.wallet
        receiver_wallet = receiver_wallet_member.wallet
        
        # Check sender wallet status
        if not sender_wallet.status or sender_wallet.status.name != "ACTIVE":
            raise serializers.ValidationError("Sender wallet is not active please contact admin.")

        # Check receiver wallet status
        if not receiver_wallet.status or receiver_wallet.status.name != "ACTIVE":
            raise serializers.ValidationError("Receiver wallet is not active please contact admin.")
        
        # Check transfer permission of sender wallet member
        if not sender_wallet_member.can_transfer:
            raise serializers.ValidationError(
                {"sender_wallet_member": "You are not allowed to transfer from this wallet."}
            )
        
        if sender_wallet_member.wallet == receiver_wallet_member.wallet:
            raise serializers.ValidationError(
                {"receiver_wallet_member": "Transfer to the same wallet is not allowed."}
            )
            
        
        # Check for wallet balance
        if sender_wallet.balance < amount:
            raise serializers.ValidationError("Insufficient balance.")
        
        # Check sender wallet debit limit
        sender_wallet_type_limits = WalletLimit.objects.filter(
            wallet=sender_wallet, 
            wallet_type_limit__entry_type="DEBIT"
        )
        if sender_wallet_type_limits.exists():
            for limit in sender_wallet_type_limits:
                if limit.remaining() < amount:
                    raise serializers.ValidationError(f"{limit.wallet_type_limit.limit_type} debit limit exceeded")
        
        # Check for sender wallet member debit limits
        sender_wallet_member_limits = WalletMemberLimit.objects.filter(wallet_member=sender_wallet_member)
        if sender_wallet_member_limits.exists():
            for limit in sender_wallet_member_limits:
                if limit.remaining() < amount:
                    raise serializers.ValidationError(f"{limit.limit_type} limit exceeded")
        
        # Check receiver wallet credit limit
        receiver_wallet_type_limits = WalletLimit.objects.filter(
            wallet=receiver_wallet,
            wallet_type_limit__entry_type="CREDIT"
        )
        if receiver_wallet_type_limits.exists():
            for limit in receiver_wallet_type_limits:
                if limit.remaining() < amount:
                    raise serializers.ValidationError(f"Receiver has '{limit.wallet_type_limit.limit_type}' credit limit exceeded")
        
        return attrs


class TransactionHistorySerializer(serializers.ModelSerializer):
    transaction_flow = serializers.SerializerMethodField()
    opponent_user = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    wallet_info = serializers.SerializerMethodField()
    transaction_type = TransactionTypeIdNameSerializer()
    class Meta:
        model = Transaction
        fields = [
            'id',
            'reference_id',
            'opponent_user',
            'amount',
            'wallet_info',
            'transaction_flow',  # DEBIT / CREDIT
            'transaction_type',
            'transaction_category',
            'status',
            'time_stamp'
        ]

    def get_transaction_flow(self, obj):
        request = self.context.get('request')
        user = request.user

        if obj.sender_user == user:
            return 'DEBIT'
        if obj.receiver_user == user:
            return 'CREDIT'
        return None

    def get_opponent_user(self, obj):
        request = self.context.get('request')
        user = request.user

        if obj.sender_user == user:
            return obj.receiver_user.full_name
        if obj.receiver_user == user:
            return obj.sender_user.full_name
        return None

    def get_wallet_info(self, obj):
        request = self.context.get('request')
        user = request.user

        if obj.sender_user == user:
            return WalletIdNameSerializer(obj.sender_wallet_member.wallet).data
        if obj.receiver_user == user:
            return WalletIdNameSerializer(obj.receiver_wallet_member.wallet).data
        return None
    
    def get_status(self, obj):
        return obj.current_status.name


class WalletLedgerSerializer(serializers.ModelSerializer):
    transaction_id = serializers.SerializerMethodField()
    sender = serializers.SerializerMethodField()
    receiver = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField() 
    class Meta:
        model = WalletLedger
        fields = [
            'id',
            'sender',
            'receiver',
            'amount',
            'entry_type',
            'transaction_id',
            'time_stamp'
        ]
    
    def get_transaction_id(self, obj):
        return obj.transaction.id
    
    def get_sender(self, obj):
        return obj.transaction.sender_user.full_name
    
    def get_receiver(self, obj):
        return obj.transaction.receiver_user.full_name

    def get_amount(self, obj):
        return obj.transaction.amount