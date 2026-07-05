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
        "Date Recorded", 
        "Date", 
        "User",
        "Transaction Type", 
        "Wallet", 
        "Category", 
        "Counterparty", 
        "Amount", 
        
      
        "Balance Before",
        "Balance After",

        "Note",  
      
    
    ]
    ws.append(headers)

    # Style the header row
    for cell in ws[1]:
        cell.font = openpyxl.styles.Font(bold=True)

    # 2. Iterate through the queryset and extract every field
    # (Removed the hardcoded "spend funds" filter so it exports whatever data the user requested)
    for tx in queryset:
        
        ws.append([
            tx.created_at.strftime("%Y-%m-%d %H:%M:%S") if tx.created_at else "",
            tx.transaction_date.strftime("%Y-%m-%d") if tx.transaction_date else "",
            
            str(tx.user) if tx.user else "", 
            tx.transaction_type,
            
            
            str(tx.wallet) if tx.wallet else "",
            
            tx.bir_category or "",
            tx.counterparty or "",
          
            float(tx.amount) if tx.amount is not None else 0.0,
           
        
            tx.wallet_balance_before or "", 
            tx.wallet_balance_after or "",

            tx.note or "",
        
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