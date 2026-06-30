from django.db.models import Sum, Q, Case, When, Value, IntegerField
from django.db.models.functions import ExtractMonth, ExtractYear

PAYROLL_CATEGORIES = ["salaries"]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

QUARTERS = ["Q1", "Q2", "Q3", "Q4"]
WEEKS = ["W1", "W2", "W3", "W4", "W5"]


def _bucket_annotation(period):
    if period == "quarterly":
        return Case(
            When(transaction_date__month__lte=3, then=Value(0)),
            When(transaction_date__month__lte=6, then=Value(1)),
            When(transaction_date__month__lte=9, then=Value(2)),
            default=Value(3),
            output_field=IntegerField(),
        )
    if period == "monthly":
        return Case(
            When(transaction_date__day__lte=7, then=Value(0)),
            When(transaction_date__day__lte=14, then=Value(1)),
            When(transaction_date__day__lte=21, then=Value(2)),
            When(transaction_date__day__lte=28, then=Value(3)),
            default=Value(4),
            output_field=IntegerField(),
        )
    return ExtractMonth("transaction_date") - 1


def _bucket_keys(period):
    if period == "quarterly":
        return QUARTERS
    if period == "monthly":
        return WEEKS
    return MONTHS


def _base_qs(queryset, period, year, month):
    if period == "monthly":
        return queryset.filter(
            transaction_date__year=year,
            transaction_date__month=month,
        )
    return queryset.filter(transaction_date__year=year)


def _build_period_result(queryset, period, year, month, value_fn):
    qs = _base_qs(queryset, period, year, month)
    keys = _bucket_keys(period)
    grouped = qs.annotate(bucket=_bucket_annotation(period)) \
        .values("bucket") \
        .annotate(**value_fn(qs)) \
        .order_by("bucket")

    lookup = {item["bucket"]: item for item in grouped}
    return [lookup.get(i, {}) for i in range(len(keys))], keys


def _entry(amount, total):
    return {
        "amount": round(float(amount), 2),
        "percentage": round(float(amount) / float(total) * 100, 2) if total > 0 else 0,
    }


def get_income_utilization(queryset, year, period="yearly", month=None):
    rows, keys = _build_period_result(
        queryset, period, year, month,
        lambda qs: {
            "income": Sum("amount", filter=Q(transaction_type="add funds")),
            "expenses": Sum("amount", filter=Q(transaction_type="spend funds")),
        },
    )

    result = {}
    for i, k in enumerate(keys):
        inc = float(rows[i].get("income") or 0)
        exp = float(rows[i].get("expenses") or 0)
        result[k] = {
            "income": round(inc, 2),
            "expenses": round(exp, 2),
            "balance": round(inc - exp, 2),
        }

    return {"income_utilization": result}


def get_payroll_vs_other_expenses(queryset, year, period="yearly", month=None):
    qs = _base_qs(queryset, period, year, month)
    keys = _bucket_keys(period)
    grouped = qs.annotate(bucket=_bucket_annotation(period)) \
        .values("bucket") \
        .annotate(
            payroll=Sum("amount", filter=Q(transaction_type="spend funds", category__in=PAYROLL_CATEGORIES)),
            other=Sum("amount", filter=Q(
                transaction_type="spend funds",
            ) & ~Q(category__in=PAYROLL_CATEGORIES)),
        ) \
        .order_by("bucket")

    lookup = {item["bucket"]: item for item in grouped}
    result = {}
    for i, k in enumerate(keys):
        row = lookup.get(i, {})
        payroll = float(row.get("payroll") or 0)
        other = float(row.get("other") or 0)
        total = payroll + other
        result[k] = {
            "payroll": _entry(payroll, total),
            "other_expenses": _entry(other, total),
        }

    return {"payroll_vs_other": result}


def get_income_vs_expenses_vs_payroll(queryset, year, period="yearly", month=None):
    rows, keys = _build_period_result(
        queryset, period, year, month,
        lambda qs: {
            "income": Sum("amount", filter=Q(transaction_type="add funds")),
            "expenses": Sum("amount", filter=Q(transaction_type="spend funds")),
        },
    )

    income = {}
    expenses = {}
    for i, k in enumerate(keys):
        income[k] = float(rows[i].get("income") or 0)
        expenses[k] = float(rows[i].get("expenses") or 0)

    return {"income": income, "expenses": expenses}


def get_funding_runaway_projection(queryset, year, period="yearly", month=None):
    totals = queryset.aggregate(
        total_income=Sum("amount", filter=Q(transaction_type="add funds")),
        total_expenses=Sum("amount", filter=Q(transaction_type="spend funds")),
    )
    balance = float(totals["total_income"] or 0) - float(totals["total_expenses"] or 0)

    monthly_net = queryset.annotate(
        y=ExtractYear("transaction_date"),
        m=ExtractMonth("transaction_date"),
    ).values("y", "m").annotate(
        income=Sum("amount", filter=Q(transaction_type="add funds")),
        expenses=Sum("amount", filter=Q(transaction_type="spend funds")),
    ).order_by("y", "m")

    labels = []
    values = []
    running = 0.0
    for item in monthly_net:
        inc = float(item["income"] or 0)
        exp = float(item["expenses"] or 0)
        running += inc - exp
        labels.append(MONTHS[item["m"] - 1] + " " + str(item["y"]))
        values.append(round(running, 2))

    labels.append("Current")
    values.append(round(balance, 2))

    if period == "monthly":
        qs = queryset.filter(
            transaction_date__year=year,
            transaction_date__month=month,
            transaction_type="spend funds",
        )
        monthly_total = qs.aggregate(total=Sum("amount"))["total"] or 0
        avg = monthly_total
        start_m = int(month)
        start_y = int(year)
    elif period == "quarterly":
        quarter = (int(month) - 1) // 3 + 1
        q_start = (quarter - 1) * 3 + 1
        q_end = quarter * 3
        qs = queryset.filter(
            transaction_date__year=year,
            transaction_date__month__gte=q_start,
            transaction_date__month__lte=q_end,
            transaction_type="spend funds",
        )
        monthly_total = qs.aggregate(total=Sum("amount"))["total"] or 0
        avg = monthly_total / 3
        start_m = q_end
        start_y = int(year)
    else:
        qs = queryset.filter(
            transaction_date__year=year,
            transaction_type="spend funds",
        )
        monthly_total = qs.aggregate(total=Sum("amount"))["total"] or 0
        months_with_data = qs.dates("transaction_date", "month").count()
        avg = monthly_total / max(months_with_data, 1)
        last = qs.dates("transaction_date", "month").last()
        if last:
            start_m = last.month
            start_y = last.year
        else:
            start_m = 1
            start_y = int(year)

    if balance > 0 and avg > 0:
        runways = balance / avg
        remaining = balance
        m = start_m
        y = start_y
        for _ in range(120):
            remaining -= avg
            if remaining <= 0:
                labels.append(MONTHS[m - 1] + " " + str(y))
                values.append(0)
                break
            m += 1
            if m > 12:
                m = 1
                y += 1
            labels.append(MONTHS[m - 1] + " " + str(y))
            values.append(round(remaining, 2))
    else:
        runways = 0

    return {
        "funding_runaway_projection": {
            "current_balance": round(balance, 2),
            "avg_monthly_expenses": round(avg, 2),
            "runway_months": round(runways, 1),
            "runway_display": f"{round(runways)} months",
            "chart": {"labels": labels, "values": values},
        }
    }


def get_incoming_by_wallet(queryset, year, month):
    qs = queryset.filter(
        transaction_type="add funds",
        transaction_date__year=year,
        transaction_date__month=month,
    ).values("wallet__name").annotate(amount=Sum("amount")).order_by("-amount")
    return {item["wallet__name"]: round(float(item["amount"]), 2) for item in qs}


def _cat_label(cat_id):
    from expenses.constants import EXPENSE_CATEGORIES_DATA
    for c in EXPENSE_CATEGORIES_DATA:
        if c["id"] == cat_id:
            return c["label"]
    return cat_id


def get_expenses_by_category(queryset, year, period="yearly", month=None):
    qs = _base_qs(queryset, period, year, month).filter(transaction_type="spend funds")
    keys = _bucket_keys(period)
    grouped = qs.annotate(bucket=_bucket_annotation(period)) \
        .values("bucket", "category") \
        .annotate(amount=Sum("amount")) \
        .order_by("bucket", "-amount")

    result = {}
    for k in keys:
        result[k] = {}
    bucket_totals = {}
    for g in grouped:
        b = g["bucket"]
        cat = g["category"]
        amt = float(g["amount"] or 0)
        key = keys[b] if b < len(keys) else None
        if key is None:
            continue
        bucket_totals[b] = bucket_totals.get(b, 0) + amt
        result[key][_cat_label(cat)] = {"amount": round(amt, 2)}

    for i, k in enumerate(keys):
        total = bucket_totals.get(i, 0) or 1
        for cat in result[k]:
            amt = result[k][cat]["amount"]
            result[k][cat]["percentage"] = round(amt / total * 100, 2)

    return result
