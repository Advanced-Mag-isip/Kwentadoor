EXPENSE_CATEGORIES_DATA = [
    {"id": "internet_phone", "label": "Internet & Phone", "bir_mapping": "Communication, Light and Water"},
    {"id": "office_supplies", "label": "Office Supplies", "bir_mapping": "Office Supplies"},
    {"id": "team_meals", "label": "Team Meals & Meetings", "bir_mapping": "Representation and Entertainment"},
    {"id": "software_tools", "label": "Software Tools & Subscriptions", "bir_mapping": "Professional Fees / Other Services"},
    {"id": "salaries", "label": "Salaries & Allowances", "bir_mapping": "Salaries and Wages"},
    {"id": "rent", "label": "Rent/Co-working Space", "bir_mapping": "Rental"},
]

# Create an O(1) lookup dictionary. 
# Result: {'internet_phone': 'Communication, Light and Water', ...}
BIR_CATEGORY_MAP = { item["id"]: item["bir_mapping"] for item in EXPENSE_CATEGORIES_DATA }