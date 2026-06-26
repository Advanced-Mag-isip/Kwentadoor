from rest_framework import serializers
from .models import User, Wallet, Transaction, Attachment, Log
from .constants import CATEGORY_LABELS

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = '__all__'

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    attachments = AttachmentSerializer(many=True, read_only=True)
    category_label = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['user']

    def get_category_label(self, obj):
        return CATEGORY_LABELS.get(obj.category, obj.category)

class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = '__all__'