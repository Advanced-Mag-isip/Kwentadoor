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
        user, created = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@example.com"},
        )
        if created:
            user.set_password("admin")
            user.save()

        wallet_defs = [
            {"name": "Petty Cash", "description": "Daily operational cash kept on hand for small business expenses and immediate purchases."},
            {"name": "Emergency Cash", "description": "Reserved cash set aside for unexpected expenses or urgent financial situations."},
            {"name": "GCash", "description": "Primary digital wallet used for mobile payments, online purchases, and fund transfers."},
            {"name": "Maya Wallet", "description": "Secondary e-wallet dedicated to online shopping, subscriptions, and digital services."},
            {"name": "UnionBank Savings", "description": "Main savings account used for storing long-term funds and personal savings."},
            {"name": "BDO Checkings", "description": "Primary checking account used for recurring bills, supplier payments, and everyday banking transactions."},
        ]

        wallets = []
        for w in wallet_defs:
            wallet, _ = Wallet.objects.get_or_create(
                name=w["name"],
                defaults={"description": w["description"]},
            )
            wallets.append(wallet)

        Transaction.objects.all().delete()

        categories = [
            "internet_phone", "office_supplies", "team_meals",
            "software_tools", "salaries", "rent", "grants_donations",
        ]

        counterparties = [
            "", "Globe Telecom", "National Bookstore", "Meralco",
            "Google Workspace", "Juan Dela Cruz", "GCash",
            "Lazada", "Grab Philippines", "PLDT",
        ]

        notes = [
            "", "Monthly payment", "One-time purchase",
            "Recurring subscription", "Office supplies",
            "Team lunch", "Quarterly grant",
        ]

        today = timezone.now().date()

        for i in range(5):
            days_ago = random.randint(0, 365)
            tx_date = today - timedelta(days=days_ago)

            cat = random.choice(categories)
            amount = round(random.uniform(50, 50000), 2)

            Transaction.objects.create(
                transaction_type="spend funds",
                user=user,
                wallet=random.choice(wallets),
                category=cat,
                transaction_date=tx_date,
                amount=amount,
                counterparty=random.choice(counterparties),
                note=random.choice(notes),
            )

        self.stdout.write(self.style.SUCCESS(f"Seeded {Transaction.objects.count()} transactions"))
