from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers
from .models import User, Wallet, Transaction, Attachment, Log, WalletTransfer, Spend
from .constants import BIR_MAPPING


class WalletSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Wallet
        fields = '__all__'


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'


class WalletTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransfer
        fields = '__all__'


class SpendSerializer(serializers.ModelSerializer):
    transaction_date = serializers.DateField(write_only=True, required=False, allow_null=True)
    note = serializers.CharField(write_only=True, required=False, allow_blank=True)
    counterparty = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Spend
        fields = '__all__'

    def create(self, validated_data):
        validated_data.pop('note', None)
        validated_data.pop('counterparty', None)
        validated_data.pop('transaction_date', None)
        return super().create(validated_data)


class TransactionSerializer(serializers.ModelSerializer):
    attachments = AttachmentSerializer(many=True, read_only=True)
    BIR_label = serializers.SerializerMethodField()
    wallet_name = serializers.CharField(source='wallet.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    DUPLICATE_WINDOW_SECONDS = 5

    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['user']

    def get_BIR_label(self, obj):
        if not obj.category:
            return None
        return BIR_MAPPING.get(obj.category, obj.category)

    def validate(self, attrs):
        tx_type = attrs.get("transaction_type")
        category = attrs.get("category")

        # --- Category fallback / integrity rules ---
        if tx_type == "add funds" and not category:
            attrs["category"] = "add_funds"

        if tx_type == "move funds" and not category:
            attrs["category"] = "transfers"

        if tx_type == "spend funds" and not category:
            raise serializers.ValidationError({
                "category": "Category is required for spend funds."
            })
        # --- Guard for double click ---
        wallet = attrs.get("wallet")
        amount = attrs.get("amount")
        if wallet is not None and amount is not None and tx_type:
            recent_cutoff = timezone.now() - timedelta(seconds=self.DUPLICATE_WINDOW_SECONDS)
            duplicate_exists = Transaction.objects.filter(
                wallet=wallet,
                transaction_type=tx_type,
                amount=amount,
                created_at__gte=recent_cutoff,
            ).exists()
            if duplicate_exists:
                raise serializers.ValidationError({
                    "non_field_errors": "Duplicate transaction detected. Please wait a moment before retrying."
                })

        return attrs


class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = '__all__'