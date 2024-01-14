from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django_pos.wsgi import *
from django_pos import settings
from django.template.loader import get_template
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from customers.models import Customer
from products.models import Product
from weasyprint import HTML, CSS
from .models import Sale, SaleDetail
import json


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

@login_required(login_url="/accounts/login/")
def SalesListView(request):
    # Specify the number of items per page
    items_per_page = 10  # You can adjust this as needed

    # Get the search query from the GET parameters
    search_query = request.GET.get('search', '')

    # Retrieve sales records based on search query and order by date_added
    all_sales = Sale.objects.filter(
        Q(customer__first_name__icontains=search_query) |
        Q(customer__last_name__icontains=search_query) |
        Q(sub_total__icontains=search_query) |
        Q(grand_total__icontains=search_query) |
        Q(tax_amount__icontains=search_query) |
        Q(tax_percentage__icontains=search_query) |
        Q(amount_payed__icontains=search_query) |
        Q(amount_change__icontains=search_query)
    ).order_by('-date_added')

    # Use Django Paginator to paginate the results
    paginator = Paginator(all_sales, items_per_page)
    page = request.GET.get('page')

    try:
        sales = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        sales = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., 9999), deliver last page of results.
        sales = paginator.page(paginator.num_pages)

    context = {
        "active_icon": "sales",
        "sales": sales,
        "search_query": search_query,
    }
    return render(request, "sales/sales.html", context=context)


@login_required(login_url="/accounts/login/")
def SalesAddView(request):
    context = {
        "active_icon": "sales",
        "customers": [c.to_select2() for c in Customer.objects.all()]
    }

    if request.method == 'POST':
        if is_ajax(request=request):
            # Save the POST arguements
            data = json.load(request)

            sale_attributes = {
                "customer": Customer.objects.get(id=int(data['customer'])),
                "sub_total": float(data["sub_total"]),
                "grand_total": float(data["grand_total"]),
                "tax_amount": float(data["tax_amount"]),
                "tax_percentage": float(data["tax_percentage"]),
                "amount_payed": float(data["amount_payed"]),
                "amount_change": float(data["amount_change"]),
            }
            try:
                # Create the sale
                new_sale = Sale.objects.create(**sale_attributes)
                new_sale.save()
                # Create the sale details
                products = data["products"]

                for product in products:
                    product_id = int(product["id"])
                    quantity = int(product["quantity"])
                    product_instance = Product.objects.get(id=product_id)

                    if product_instance.quantity < quantity:
                        new_sale.delete()
                        messages.error(
                            request, f'Insufficient quantity for product: {product_instance.name}', extra_tags="danger")
                        return redirect('sales:sales_list')

                    product_instance.quantity -= quantity
                    product_instance.save()

                    detail_attributes = {
                        "sale": Sale.objects.get(id=new_sale.id),
                        "product": Product.objects.get(id=int(product["id"])),
                        "price": product["price"],
                        "quantity": product["quantity"],
                        "total_detail": product["total_product"]
                    }
                    sale_detail_new = SaleDetail.objects.create(
                        **detail_attributes)
                    sale_detail_new.save()

                print("Sale saved")

                messages.success(
                    request, 'Sale created succesfully!', extra_tags="success")

            except Exception as e:
                messages.success(
                    request, 'There was an error during the creation!', extra_tags="danger")

        return redirect('sales:sales_list', refresh='true')

    return render(request, "sales/sales_add.html", context=context)


@login_required(login_url="/accounts/login/")
def SalesDetailsView(request, sale_id):
    """
    Args:
        sale_id: ID of the sale to view
    """
    try:
        # Get tthe sale
        sale = Sale.objects.get(id=sale_id)

        # Get the sale details
        details = SaleDetail.objects.filter(sale=sale)

        context = {
            "active_icon": "sales",
            "sale": sale,
            "details": details,
        }
        return render(request, "sales/sales_details.html", context=context)
    except Exception as e:
        messages.success(
            request, 'There was an error getting the sale!', extra_tags="danger")
        print(e)
        return redirect('sales:sales_list')


@login_required(login_url="/accounts/login/")
def ReceiptPDFView(request, sale_id):
    """
    Args:
        sale_id: ID of the sale to view the receipt
    """
    # Get tthe sale
    sale = Sale.objects.get(id=sale_id)

    # Get the sale details
    details = SaleDetail.objects.filter(sale=sale)

    template = get_template("sales/sales_receipt_pdf.html")
    context = {
        "sale": sale,
        "details": details
    }
    html_template = template.render(context)

    # CSS Boostrap
    css_url = os.path.join(
        settings.BASE_DIR, 'static/css/receipt_pdf/bootstrap.min.css')

    # Create the pdf
    pdf = HTML(string=html_template).write_pdf(stylesheets=[CSS(css_url)])

    return HttpResponse(pdf, content_type="application/pdf")
