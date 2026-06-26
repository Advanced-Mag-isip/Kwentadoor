from rest_framework import serializers
from .models import User, Wallet, Transaction, Attachment, Log

# Helper dictionary to map the stored ID to the friendly label
CATEGORY_LABELS = {
    "internet_phone": "Internet & Phone",
    "office_supplies": "Office Supplies",
    "team_meals": "Team Meals & Meetings",
    "software_tools": "Software Tools & Subscriptions",
    "salaries": "Salaries & Allowances",
    "rent": "Rent/Co-working Space",
    "grants_donations": "Grants / Donations Received",
}

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
    
    # Add a read-only field that automatically returns the friendly label
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