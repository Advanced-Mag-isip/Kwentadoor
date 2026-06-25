from rest_framework import serializers
from .models import User, Wallet, Transaction, Attachment, Log

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
    
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['user']

class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = '__all__'