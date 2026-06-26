EXPENSE_CATEGORIES_DATA = [
    {
        "id": "internet_phone",
        "label": "Internet & Phone",
        "bir_mapping": "Communication, Light and Water"
    },
    {
        "id": "office_supplies",
        "label": "Office Supplies",
        "bir_mapping": "Office Supplies"
    },
    {
        "id": "team_meals",
        "label": "Team Meals & Meetings",
        "bir_mapping": "Representation and Entertainment"
    },
    {
        "id": "software_tools",
        "label": "Software Tools & Subscriptions",
        "bir_mapping": "Professional Fees / Other Services"
    },
    {
        "id": "salaries",
        "label": "Salaries & Allowances",
        "bir_mapping": "Salaries and Wages"
    },
    {
        "id": "rent",
        "label": "Rent/Co-working Space",
        "bir_mapping": "Rental"
    },
    {
        "id": "grants_donations",
        "label": "Grants / Donations Received",
        "bir_mapping": "Grants / Donations"
    },
]

CATEGORY_CHOICES = [(cat["id"], cat["label"]) for cat in EXPENSE_CATEGORIES_DATA]
BIR_MAPPING = {cat["id"]: cat["bir_mapping"] for cat in EXPENSE_CATEGORIES_DATA}

TRANSACTION_TYPE_CHOICES = [
    ("add funds", "Add Funds"),
    ("spend funds", "Spend Funds"),
    ("move funds", "Move Funds"),
]