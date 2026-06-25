from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from expenses.models import Wallet, Transaction
from datetime import date, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with sample expenses data"

    def handle(self, *args, **options):
        user, _ = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@example.com"},
        )

        wallets = []
        for name in ["Personal", "Business", "Savings"]:
            wallet, _ = Wallet.objects.get_or_create(
                name=name,
                defaults={"description": f"{name} wallet"},
            )
            wallets.append(wallet)

        Transaction.objects.all().delete()

        categories = {
            "income": ["Salary", "Freelance", "Investment", "Refund", "Allowance"],
            "expense": ["Food", "Transport", "Rent", "Utilities", "Entertainment", "Healthcare", "Shopping", "Education"],
        }

        today = timezone.now().date()

        for i in range(200):
            days_ago = random.randint(0, 365)
            tx_date = today - timedelta(days=days_ago)

            tx_type = random.choices(["income", "expense"], weights=[30, 70])[0]
            cat = random.choice(categories[tx_type])

            if tx_type == "income":
                amount = round(random.uniform(100, 50000), 2)
            else:
                amount = round(random.uniform(10, 15000), 2)

            Transaction.objects.create(
                transaction_type=tx_type,
                user=user,
                wallet=random.choice(wallets),
                category=cat,
                transaction_date=tx_date,
                amount=amount,
                counterparty=random.choice(["", "Acme Corp", "Grocery Store", "Landlord", "Client A", "Shopee", "Grab"]),
                note=random.choice(["", "Monthly payment", "One-time purchase", "Recurring", "Refund"]),
            )

        self.stdout.write(self.style.SUCCESS(f"Seeded {Transaction.objects.count()} transactions"))
