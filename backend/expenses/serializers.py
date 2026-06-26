from rest_framework import serializers
from .models import User, Wallet, Transaction, Attachment, Log
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

class TransactionSerializer(serializers.ModelSerializer):
    attachments = AttachmentSerializer(many=True, read_only=True)
    BIR_label = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['user']

    def get_BIR_label(self, obj):
        return BIR_MAPPING.get(obj.category, obj.category)

class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = '__all__'