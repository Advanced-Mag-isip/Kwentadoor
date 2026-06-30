from django.db.models import Sum, Avg, Q
from expenses.models import Attachment


PAYROLL_CATEGORIES = ["salaries"]


def get_monthly_summary(queryset, year, month):
    current = _period_expenses(queryset, year, month, month)
    previous = _period_expenses(queryset, year, month - 1, month - 1)
    if month == 1:
        previous = _period_expenses(queryset, year - 1, 12, 12)

    return {
        "year": int(year),
        "month": int(month),
        "total_incoming_funds": float(current["total_incoming_funds"]),
        "total_outgoing_funds": float(current["total_outgoing_funds"]),
        "average_incoming_funds": float(current["average_incoming_funds"]),
        "average_outgoing_funds": float(current["average_outgoing_funds"]),
        "total_payroll_cost": float(current["total_payroll_cost"]),
        "total_missing_receipts": current["total_missing_receipts"],
        "undocumented_expenses_pct": current["undocumented_expenses_pct"],
        "expense_growth": _growth(current["total_outgoing_funds"], previous["total_outgoing_funds"]),
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
        "total_incoming_funds": float(current["total_incoming_funds"]),
        "total_outgoing_funds": float(current["total_outgoing_funds"]),
        "average_incoming_funds": float(current["average_incoming_funds"]),
        "average_outgoing_funds": float(current["average_outgoing_funds"]),
        "total_payroll_cost": float(current["total_payroll_cost"]),
        "total_missing_receipts": current["total_missing_receipts"],
        "undocumented_expenses_pct": current["undocumented_expenses_pct"],
        "expense_growth": _growth(current["total_outgoing_funds"], previous["total_outgoing_funds"]),
    }


def get_yearly_summary(queryset, year):
    qs = queryset.filter(transaction_date__year=year)
    qs = qs.values("transaction_date__year").annotate(
        total_income=Sum("amount", filter=Q(transaction_type="add funds")),
        total_expenses=Sum("amount", filter=Q(transaction_type="spend funds")),
        average_income=Avg("amount", filter=Q(transaction_type="add funds")),
        average_expenses=Avg("amount", filter=Q(transaction_type="spend funds")),
    ).order_by("transaction_date__year")

    results = []
    for item in qs:
        y = item["transaction_date__year"]
        prev_total = _period_expenses(queryset, y - 1, 1, 12)["total_outgoing_funds"]
        yr_stats = _period_expenses(queryset, y, 1, 12)
        results.append({
            "year": y,
            "total_incoming_funds": float(item["total_income"] or 0),
            "total_outgoing_funds": float(item["total_expenses"] or 0),
            "average_incoming_funds": float(item["average_income"] or 0),
            "average_outgoing_funds": float(item["average_expenses"] or 0),
            "total_payroll_cost": float(yr_stats["total_payroll_cost"]),
            "total_missing_receipts": yr_stats["total_missing_receipts"],
            "undocumented_expenses_pct": yr_stats["undocumented_expenses_pct"],
            "expense_growth": _growth(float(item["total_expenses"] or 0), prev_total),
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
        total_income=Sum("amount", filter=Q(transaction_type="add funds")),
        total_expenses=Sum("amount", filter=Q(transaction_type="spend funds")),
        average_income=Avg("amount", filter=Q(transaction_type="add funds")),
        average_expenses=Avg("amount", filter=Q(transaction_type="spend funds")),
        total_payroll=Sum("amount", filter=Q(
            transaction_type="spend funds",
            category__in=PAYROLL_CATEGORIES,
        )),
    )

    expense_qs = qs.filter(transaction_type="spend funds")
    total_expense_count = expense_qs.count()
    exp_with_rcpt = Attachment.objects.filter(transaction__in=expense_qs).values("transaction").distinct().count()
    missing = total_expense_count - exp_with_rcpt

    return {
        "total_incoming_funds": stats["total_income"] or 0,
        "total_outgoing_funds": stats["total_expenses"] or 0,
        "average_incoming_funds": stats["average_income"] or 0,
        "average_outgoing_funds": stats["average_expenses"] or 0,
        "total_payroll_cost": stats["total_payroll"] or 0,
        "total_missing_receipts": missing,
        "undocumented_expenses_pct": round(
            missing / total_expense_count * 100, 2
        ) if total_expense_count > 0 else 0.0,
    }


def _growth(current, previous):
    if previous == 0:
        return None if current == 0 else 100.0
    return round((float(current) - float(previous)) / float(previous) * 100, 2)
