# Analytics

## Overview

The `analytics` app provides summary endpoints for expense/income data. It queries the `expenses` app models and returns aggregated totals filtered by period.

## API Endpoints

### `GET /api/analytics/summary/`

Returns total income and total expenses for a given period.

#### Authentication

Requires authentication. Supports:
- Basic Auth (`username:password` base64-encoded)
- Token Auth (`Authorization: Token <key>`)
- Session Auth (browser login)

**Getting your auth token:**
```powershell
cd backend
venv\Scripts\Activate.ps1
python manage.py shell -c "from rest_framework.authtoken.models import Token; from expenses.models import User; t, _ = Token.objects.get_or_create(user=User.objects.get(username='admin')); print(t.key)"
```
Or visit `/admin/authtoken/token/` after logging into the Django admin.

#### Query Parameters

| Parameter | Type   | Default        | Description |
|-----------|--------|----------------|-------------|
| `period`  | string | `"monthly"`    | One of: `monthly`, `quarterly`, `yearly` |
| `year`    | int    | current year   | Filter year (e.g. `2026`) |
| `month`   | int    | current month  | Filter month `1–12` (used for monthly & quarterly) |

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `total_income` | float | Sum of all income transactions |
| `total_expenses` | float | Sum of all expense transactions |
| `average_income` | float | Average income per transaction |
| `average_expenses` | float | Average expense per transaction |
| `expense_growth` | float or null | % change in expenses vs previous period |
| `missing_receipt_count` | int | Number of expense transactions without attachments |
| `undocumented_expenses_pct` | float | % of expense transactions missing receipts |
| `runaway` | object or null | `{"year": 2026, "month": 6}` — year and month of the most recent transaction |

#### Responses

**Monthly**
```json
GET /api/analytics/summary/?period=monthly&year=2026&month=6
```
```json
{
  "year": 2026,
  "month": 6,
  "total_income": 128216.68,
  "total_expenses": 33449.17,
  "average_income": 2003.39,
  "average_expenses": 245.95,
  "expense_growth": -32.99,
  "missing_receipt_count": 6,
  "undocumented_expenses_pct": 100.0,
  "runaway": {"year": 2026, "month": 6}
}
```

**Quarterly**
```json
GET /api/analytics/summary/?period=quarterly&year=2026&month=6
```
```json
{
  "year": 2026,
  "quarter": 2,
  "total_income": 452488.57,
  "total_expenses": 206807.28,
  "average_income": 8227.06,
  "average_expenses": 1897.31,
  "expense_growth": -11.88,
  "missing_receipt_count": 26,
  "undocumented_expenses_pct": 100.0,
  "runaway": {"year": 2026, "month": 6}
}
```

**Yearly**
```json
GET /api/analytics/summary/?period=yearly&year=2026
```
```json
[
  {
    "year": 2026,
    "total_income": 845816.46,
    "total_expenses": 441499.31,
    "average_income": 13215.88,
    "average_expenses": 3246.32,
    "expense_growth": -16.93,
    "missing_receipt_count": 60,
    "undocumented_expenses_pct": 100.0,
    "runaway": false
  }
]
```

---

### Common Query Parameters

All chart endpoints support these optional parameters for period filtering:

| Parameter | Type   | Default    | Description |
|-----------|--------|------------|-------------|
| `period`  | string | `"yearly"` | One of: `monthly`, `quarterly`, `yearly` |
| `year`    | int    | current    | Filter year (e.g. `2026`) |
| `month`   | int    | —          | Required if `period=monthly` or `period=quarterly` (`1–12`) |

---

### `GET /api/analytics/charts/income-utilization/`

Returns income, expenses, and balance — compatible with bar charts.

#### Response (yearly)

```json
{
  "income_utilization": {
    "income": 845816.46,
    "expenses": 441499.31,
    "balance": 404317.15
  }
}
```

**Monthly example:** `?period=monthly&year=2026&month=1`
```json
{"income_utilization":{"income":107740.88,"expenses":61936.45,"balance":45804.43}}
```

**Quarterly example:** `?period=quarterly&year=2026&month=2`
```json
{"income_utilization":{"income":393327.89,"expenses":234692.03,"balance":158635.86}}
```

---

### `GET /api/analytics/charts/payroll-vs-other/`

Returns payroll vs other expenses breakdown — compatible with pie charts.

#### Response (yearly)

```json
{
  "payroll": {"amount": 0.0, "percentage": 0.0},
  "other_expenses": {"amount": 441499.31, "percentage": 100.0}
}
```

Payroll categories are: `payroll`, `salary`, `wages`, `compensation` (case-insensitive match on the transaction `category` field).

---

### `GET /api/analytics/charts/income-vs-expenses/`

Returns income vs expenses data — structured for line charts.

#### Response (yearly)

```json
{
  "income": {"Jan": 107740.88, "Feb": 103695.04, "Mar": 181891.97, ...},
  "expenses": {"Jan": 61936.45, "Feb": 111144.53, "Mar": 61611.05, ...}
}
```

**Monthly example:** `?period=monthly&year=2026&month=6`
```json
{"income":{"Jun":128216.68},"expenses":{"Jun":33449.17}}
```

**Quarterly example:** `?period=quarterly&year=2026&month=5`
```json
{"income":{"Q2":452488.57},"expenses":{"Q2":206807.28}}
```

---

### `GET /api/analytics/charts/expenses-by-category/`

Returns expenses grouped by category with amounts and percentages — for bar charts.

#### Response (yearly)

```json
{
  "transport": {"amount": 108330.12, "percentage": 24.54},
  "entertainment": {"amount": 68627.0, "percentage": 15.54},
  "utilities": {"amount": 55374.74, "percentage": 12.54}
}
```

**Quarterly example:** `?period=quarterly&year=2026&month=4`
```json
{
  "transport": {"amount": 63481.23, "percentage": 30.7},
  "education": {"amount": 44632.72, "percentage": 21.58},
  ...
}
```

---

### `GET /api/analytics/charts/funding-runaway-projection/`

Returns cumulative funding balance projection — structured for line charts.

#### Response (yearly)

```json
{
  "funding_runaway_projection": {"Jan": 230150.31, "Feb": 222700.82, "Mar": 342981.74, ...}
}
```

**Monthly example:** `?period=monthly&year=2026&month=3`
```json
{"funding_runaway_projection":{"Mar":304626.8}}
```

**Quarterly example:** `?period=quarterly&year=2026&month=6`
```json
{"funding_runaway_projection":{"Q2":588663.03}}
```

## How to Run

### 1. Start the backend server

```bash
cd backend
venv\Scripts\Activate.ps1
python manage.py runserver
```

The server starts at `http://localhost:8000`.

### 2. Test the API

**Using real curl** (e.g. Git Bash, WSL, or `curl.exe`):
```bash
curl -u admin:admin "http://localhost:8000/api/analytics/summary/?period=monthly&year=2026&month=6"
curl -u admin:admin "http://localhost:8000/api/analytics/charts/income-utilization/?year=2026"
```

**Using PowerShell's `Invoke-WebRequest`** (replace `YWRtaW46YWRtaW4=` with your Base64-encoded `user:pass`):
```powershell
$auth = @{Authorization="Basic YWRtaW46YWRtaW4="}
Invoke-WebRequest -Uri "http://localhost:8000/api/analytics/summary/?period=monthly&year=2026&month=6" -Headers $auth -UseBasicParsing | Select-Object -ExpandProperty Content
```

**Using an auth token** (replace `TOKEN` with your key):
```powershell
$auth = @{Authorization="Token d3115e82f9bc1a6b894d77e3d6a13bbf213bf9c5"}
Invoke-WebRequest -Uri "http://localhost:8000/api/analytics/charts/income-utilization/?year=2026" -Headers $auth -UseBasicParsing | Select-Object -ExpandProperty Content
```

**Endpoints** (browsable docs with live Fetch buttons):
```
http://localhost:8000/api/analytics/endpoints/
```

## Project Structure

```
analytics/
├── services/
│   ├── __init__.py
│   ├── summary.py          # summary computation and filtering logic
│   ├── chart.py            # chart data services (all chart endpoints)
│   └── util.py             # shared period-filtering helper
├── views/
│   ├── __init__.py
│   ├── summary.py          # summary endpoint view
│   ├── chart.py            # all chart endpoint views
│   └── endpoints.py        # browsable endpoints listing
├── templates/
│   └── analytics/
│       └── endpoints.html  # live docs page with clickable Fetch buttons
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── urls.py                 # routes all analytics endpoints
└── README.md
```

## Seed Data

To populate the database with sample transactions:

```bash
python manage.py seed_expenses
```
