from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from expenses.models import Wallet

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with sample wallets"

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

        for w in wallet_defs:
            Wallet.objects.get_or_create(
                name=w["name"],
                defaults={"description": w["description"]},
            )

        self.stdout.write(self.style.SUCCESS(f"Seeded {Wallet.objects.count()} wallets"))
