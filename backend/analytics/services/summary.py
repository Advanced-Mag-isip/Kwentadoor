from django.db.models import Sum, Avg, Q, Count
from analytics.services.chart import get_funding_runaway_projection


def get_monthly_summary(queryset, year, month):
    current = _period_expenses(queryset, year, month, month)
    previous = _period_expenses(queryset, year, month - 1, month - 1)
    if month == 1:
        previous = _period_expenses(queryset, year - 1, 12, 12)

    return {
        "year": int(year),
        "month": int(month),
        "total_income": float(current["total_income"]),
        "total_expenses": float(current["total_expenses"]),
        "average_income": float(current["average_income"]),
        "average_expenses": float(current["average_expenses"]),
        "expense_growth": _growth(current["total_expenses"], previous["total_expenses"]),
        "missing_receipt_count": current["missing_receipt_count"],
        "undocumented_expenses_pct": current["undocumented_expenses_pct"],
        "runaway": _compute_runway(queryset, "monthly", year, month),
    }


def get_quarterly_summary(queryset, year, month):
    quarter = (int(month) - 1) // 3 + 1
    q_start = (quarter - 1) * 3 + 1
    q_end = quarter * 3

    current = _period_expenses(queryset, year, q_start, q_end)

    prev_q_start = q_start - 3
    prev_q_end = q_end - 3
    if prev_q_start < 1:
        prev_q_start += 12
        prev_q_end += 12
        prev_year = year - 1
    else:
        prev_year = year
    previous = _period_expenses(queryset, prev_year, prev_q_start, prev_q_end)

    return {
        "year": int(year),
        "quarter": quarter,
        "total_income": float(current["total_income"]),
        "total_expenses": float(current["total_expenses"]),
        "average_income": float(current["average_income"]),
        "average_expenses": float(current["average_expenses"]),
        "expense_growth": _growth(current["total_expenses"], previous["total_expenses"]),
        "missing_receipt_count": current["missing_receipt_count"],
        "undocumented_expenses_pct": current["undocumented_expenses_pct"],
        "runaway": _compute_runway(queryset, "quarterly", year, month),
    }


def get_yearly_summary(queryset, year):
    qs = queryset.filter(transaction_date__year=year)
    qs = qs.values("transaction_date__year").annotate(
        total_income=Sum("amount", filter=Q(transaction_type="income")),
        total_expenses=Sum("amount", filter=Q(transaction_type="expense")),
        average_income=Avg("amount", filter=Q(transaction_type="income")),
        average_expenses=Avg("amount", filter=Q(transaction_type="expense")),
    ).order_by("transaction_date__year")

    results = []
    for item in qs:
        y = item["transaction_date__year"]
        prev_total = _period_expenses(queryset, y - 1, 1, 12)["total_expenses"]
        yr_stats = _period_expenses(queryset, y, 1, 12)
        results.append({
            "year": y,
            "total_income": float(item["total_income"] or 0),
            "total_expenses": float(item["total_expenses"] or 0),
            "average_income": float(item["average_income"] or 0),
            "average_expenses": float(item["average_expenses"] or 0),
            "expense_growth": _growth(float(item["total_expenses"] or 0), prev_total),
            "missing_receipt_count": yr_stats["missing_receipt_count"],
            "undocumented_expenses_pct": yr_stats["undocumented_expenses_pct"],
            "runaway": _compute_runway(queryset, "yearly", y),
        })

    return results


def _period_expenses(queryset, year, month_start, month_end):
    if month_start > month_end:
        qs = queryset.filter(
            Q(transaction_date__year=year, transaction_date__month__gte=month_start) |
            Q(transaction_date__year=year + 1, transaction_date__month__lte=month_end)
        )
    else:
        qs = queryset.filter(
            transaction_date__year=year,
            transaction_date__month__gte=month_start,
            transaction_date__month__lte=month_end,
        )

    stats = qs.aggregate(
        total_income=Sum("amount", filter=Q(transaction_type="income")),
        total_expenses=Sum("amount", filter=Q(transaction_type="expense")),
        average_income=Avg("amount", filter=Q(transaction_type="income")),
        average_expenses=Avg("amount", filter=Q(transaction_type="expense")),
    )

    expense_qs = qs.filter(transaction_type="expense")
    total_expense_count = expense_qs.count()
    exp_with_rcpt = expense_qs.annotate(
        rcpt_count=Count("attachments")
    ).filter(rcpt_count__gt=0).count()
    missing = total_expense_count - exp_with_rcpt

    return {
        "total_income": stats["total_income"] or 0,
        "total_expenses": stats["total_expenses"] or 0,
        "average_income": stats["average_income"] or 0,
        "average_expenses": stats["average_expenses"] or 0,
        "missing_receipt_count": missing,
        "undocumented_expenses_pct": round(
            missing / total_expense_count * 100, 2
        ) if total_expense_count > 0 else 0.0,
    }


def _compute_runway(queryset, period, year, month=None):
    proj = get_funding_runaway_projection(queryset, year, period, month)
    d = proj.get("funding_runaway_projection", {})
    return d.get("runway_display", "0 months")


def _growth(current, previous):
    if previous == 0:
        return None if current == 0 else 100.0
    return round((float(current) - float(previous)) / float(previous) * 100, 2)
