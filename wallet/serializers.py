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

class WalletToWalletTransferInputSerializer(serializers.Serializer):
    money_request = serializers.PrimaryKeyRelatedField(queryset=MoneyRequest.objects.filter(current_status__name="REQUESTED"))
    sender_wallet_member = serializers.PrimaryKeyRelatedField(queryset=WalletMember.objects.filter(can_transfer=True))
    summary = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs, *args, **kwargs):
        super().validate(attrs)
        
        sender_wallet_member = attrs.get('sender_wallet_member')
        money_request_obj = attrs.get('money_request')
        receiver_wallet_member = money_request_obj.request_wallet_member
        amount = money_request_obj.amount
        
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


class UserBasicInfoOutputSerializer(serializers.ModelSerializer):
    country = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    district = serializers.SerializerMethodField()
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'full_name',
            'contact_no',
            'country',
            'state',
            'district'
        ]
    
    def get_country(self, obj):
        residential = obj.current_residential_details
        if residential and residential.country:
            return residential.country.name
        return None
    
    def get_state(self, obj):
        residential = obj.current_residential_details
        if residential and residential.state:
            return residential.state.name
        return None
    
    def get_district(self, obj):
        residential = obj.current_residential_details
        if residential and residential.district:
            return residential.district.name
        return None

class WalletMemberInfoOutputSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()
    # email = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    district = serializers.SerializerMethodField()
    class Meta:
        model = WalletMember
        fields = [
            'id',
            'fullname',
            # 'email',
            'country',
            'state',
            'district'
        ]
    
    def get_fullname(self, obj):
        return obj.user.full_name

    # def get_email(self, obj):
    #     return obj.user.email
    
    def get_country(self, obj):
        residential = obj.user.current_residential_details
        if residential and residential.country:
            return residential.country.name
        return None
    
    def get_state(self, obj):
        residential = obj.user.current_residential_details
        if residential and residential.state:
            return residential.state.name
        return None
    
    def get_district(self, obj):
        residential = obj.user.current_residential_details
        if residential and residential.district:
            return residential.district.name
        return None


class MoneyRequestInputSerializer(serializers.ModelSerializer):
    payer_user = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(is_verified=True),
        required=True
    )
    class Meta:
        model = MoneyRequest
        fields = [
            'request_wallet_member',
            'payer_user',
            'amount',
            'summary'
        ]
        extra_kwargs = {
            'request_wallet_member': {'required': True},
        }

    def validate(self, attrs):
        super().validate(attrs)
        
        logged_user = self.context.get('logged_user')
        request_wallet_member_obj = attrs.get('request_wallet_member')
        payer_user_obj = attrs.get('payer_user')
        amount = attrs.get('amount')
        
        if request_wallet_member_obj.user != logged_user:
            raise serializers.ValidationError({"error": "You do not have access to this wallet."})
        
        if payer_user_obj == logged_user:
            raise serializers.ValidationError({"error": "You cannot request money from yourself."})
        
        # Check amount
        if amount.as_tuple().exponent < -2:
            raise serializers.ValidationError("Amount supports max 2 decimal places.")
        
        if amount <= 0:
            raise serializers.ValidationError({"amount": "Amount must be greater than 0."})
                
        return attrs


class MoneyRequestOutputSerializerForRequester(serializers.ModelSerializer):
    payer_wallet_member = WalletMemberInfoOutputSerializer()
    status = serializers.SerializerMethodField()
    class Meta:
        model = MoneyRequest
        fields = [
            'id',
            'payer_wallet_member',
            'amount',
            'summary',
            'status',
            'time_stamp'
        ]
    
    def get_status(self, obj):
        return obj.current_status.name


class MoneyRequestOutputSerializerForPayer(serializers.ModelSerializer):
    request_wallet_member = WalletMemberInfoOutputSerializer()
    status = serializers.SerializerMethodField()
    class Meta:
        model = MoneyRequest
        fields = [
            'id',
            'request_wallet_member',
            'payer_wallet_member',
            'amount',
            'summary',
            'status',
            'time_stamp'
        ]
    
    def get_status(self, obj):
        return obj.current_status.name