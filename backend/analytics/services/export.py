import openpyxl
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Sum
from xhtml2pdf import pisa
from .constants import BIR_CATEGORY_MAP

def export_transactions_to_xlsx(queryset, period_label):
    # Create an in-memory workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Transactions"

    # 1. Define all columns based strictly on your Transaction model
    headers = [
        "ID", 
        "Transaction Type", 
        "User", 
        "Wallet", 
        "BIR Category", 
        "Date", 
        "Amount", 
        "Counterparty", 
        "Note", 
        "Balance Before",
        "Balance After", 
        "Created At", 
        "Updated At"
    ]
    ws.append(headers)

    # Style the header row
    for cell in ws[1]:
        cell.font = openpyxl.styles.Font(bold=True)

    # 2. Iterate through the queryset and extract every field
    # (Removed the hardcoded "spend funds" filter so it exports whatever data the user requested)
    for tx in queryset:
        
        ws.append([
            tx.id,
            tx.transaction_type,
            
            # Using str() safely handles ForeignKeys in case they are null
            str(tx.user) if tx.user_id else "", 
            str(tx.wallet) if tx.wallet_id else "",
            
            tx.bir_category or "",
            tx.transaction_date.strftime("%Y-%m-%d") if tx.transaction_date else "",
            float(tx.amount) if tx.amount is not None else 0.0,
            tx.counterparty or "",
            tx.note or "",
            
            # For optional foreign keys, grabbing the ID directly is the safest/fastest method
            tx.wallet_balance_before or "", 
            tx.wallet_balance_after or "",
            
            # Formatting timestamps so Excel can read them easily
            tx.created_at.strftime("%Y-%m-%d %H:%M:%S") if tx.created_at else "",
            tx.updated_at.strftime("%Y-%m-%d %H:%M:%S") if tx.updated_at else "",
        ])

    # 3. Build and return the response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="transactions_export_{period_label}.xlsx"'
    wb.save(response)
    return response

def export_summary_to_pdf(summary_data, queryset, period_label):
    # Calculate top 5 categories
    category_breakdown = list(queryset.filter(transaction_type="spend funds") \
        .values('category') \
        .annotate(total=Sum('amount')) \
        .order_by('-total')[:5])

    # Inject the BIR mapping into the aggregated dictionaries
    for cat in category_breakdown:
        cat['bir_category'] = BIR_CATEGORY_MAP.get(cat['category'], "Uncategorized/Other")

    context = {
        'summary': summary_data,
        'categories': category_breakdown,
        'period_label': period_label,
        'transactions': queryset.order_by('-transaction_date') 
    }

    # Render HTML
    html_string = render_to_string('analytics/pdf_report.html', context)
    
    # Create the HTTP response with PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="financial_report_{period_label}.pdf"'

    # Convert HTML to PDF and write it directly to the response
    pisa_status = pisa.CreatePDF(html_string, dest=response)

    # Return error response if something went wrong
    if pisa_status.err:
        return HttpResponse(f'We had some errors generating the PDF <pre>{html_string}</pre>')
        
    return response