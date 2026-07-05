INCOME_CATEGORIES_DATA = [
    {"id": "capital_injection", "label": "Capital Injection", "bir_mapping": "Capital Injection"},
    {"id": "generic_income", "label": "Generic", "bir_mapping": "Generic"},
    {
        "id": "grants_donations",
        "label": "Grants / Donations Received",
        "bir_mapping": "Grants / Donations"
    },
    {"id": "income", "label" : "Income", "bir_mapping" : "income"}, 
    {"id": "payment_for_services ", "label" : "Payment for Services", "bir_mapping" : "Payment for Services"}, 
    {"id": "payment_for_comissions ", "label" : "Payment for Comissions", "bir_mapping" : "Payment for Comissions"}, 


]

TRANSFER_CATEGORIES_DATA = [
    {"id": "transfers", "label": "Transfers", "bir_mapping": "Transfers"},
]

EXPENSE_CATEGORIES_DATA = [
    {"id": "internet_phone", "label": "Internet & Phone", "bir_mapping": "Communication, Light and Water"},
    {"id": "office_supplies", "label": "Office Supplies", "bir_mapping": "Office Supplies"},
    {"id": "team_meals", "label": "Team Meals & Meetings", "bir_mapping": "Representation and Entertainment"},
    {"id": "software_tools", "label": "Software Tools & Subscriptions", "bir_mapping": "Professional Fees / Other Services"},
    {"id": "salaries", "label": "Salaries & Allowances", "bir_mapping": "Salaries and Wages"},
    {"id": "rent", "label": "Rent/Co-working Space", "bir_mapping": "Rental"},
    {"id": "capital_injection", "label": "Capital Injection", "bir_mapping": "Capital Injection"},
    {"id": "generic_income", "label": "Generic", "bir_mapping": "Generic"},
    {"id": "grants_donations", "label": "Grants / Donations Received", "bir_mapping": "Grants / Donations"},
    {"id": "income", "label" : "Income", "bir_mapping" : "income"}, 
    {"id": "payment_for_services", "label" : "Payment for Services", "bir_mapping" : "Payment for Services"}, 
    {"id": "payment_for_commissions", "label" : "Payment for Commissions", "bir_mapping" : "Payment for Commissions"}, 
]

# Create an O(1) lookup dictionary. 
BIR_CATEGORY_MAP = { item["id"]: item["bir_mapping"] for item in EXPENSE_CATEGORIES_DATA }

ALL_CATEGORIES_DATA = INCOME_CATEGORIES_DATA + EXPENSE_CATEGORIES_DATA + TRANSFER_CATEGORIES_DATA
CATEGORY_CHOICES = [(cat["id"], cat["label"]) for cat in ALL_CATEGORIES_DATA]
BIR_MAPPING = {cat["id"]: cat["bir_mapping"] for cat in ALL_CATEGORIES_DATA}
CATEGORY_MAP = {cat["id"]: cat for cat in ALL_CATEGORIES_DATA}

TRANSACTION_TYPE_CHOICES = [
    ('add funds', 'Add Funds'),
    ('spend funds', 'Spend Funds'),
    ('transfer out', 'Transfer Out'), # New
    ('transfer in', 'Transfer In'),   # New
]
