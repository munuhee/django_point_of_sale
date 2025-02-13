import os
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import get_template
from django_pos.wsgi import *
from django_pos import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
from django.db.models import Q
from django.db import models
from django.http import JsonResponse

from io import BytesIO
from django.views import View
from xhtml2pdf import pisa

from customers.models import Customer
from products.models import Product
from .models import Sale, SaleDetail, Tax
from .forms import TaxForm
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import json

def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

@login_required(login_url="/accounts/login/")
def SalesListView(request):
    # Specify the number of items per page
    items_per_page = 15  # You can adjust this as needed

    # Get the search query from the GET parameters
    search_query = request.GET.get('search', '')

    # Retrieve sales records based on search query and order by date_added
    all_sales = Sale.objects.filter(
        Q(customer__first_name__icontains=search_query) |
        Q(customer__last_name__icontains=search_query) |
        Q(sub_total__icontains=search_query) |
        Q(grand_total__icontains=search_query) |
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
                "discount_amount": float(data["discount_amount"]),
                "discount_percentage": float(data["discount_percentage"]),
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

                     # Check if the quantity is valid
                    if product_instance.quantity < quantity:
                        # Return a JSON response with an error message
                        new_sale.delete()
                        return JsonResponse({'error': 'Insufficient quantity available for ' + product_instance.name})

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

                # Calculate loyalty points based on the grand total
                loyalty_points = int(new_sale.grand_total // 100)  # You can adjust this formula as needed

                # Update customer loyalty points
                customer = new_sale.customer
                customer.loyalty_points += loyalty_points
                customer.save()

                print("Sale saved")

                messages.success(
                    request, 'Sale created succesfully!', extra_tags="success")
                # Return the sale ID in the JSON response
                return JsonResponse({'sale_id': new_sale.id})

                # Redirect to the sales details page for the newly created sale
                return redirect(reverse('sales:sales_details', kwargs={'sale_id': new_sale.id}))

            except Exception as e:
                messages.success(
                    request, 'There was an error during the creation!', extra_tags="danger")
                return redirect('sales:sales_list')

    return render(request, "sales/sales_add.html", context=context)

@login_required(login_url="/accounts/login/")
def SalesDetailsView(request, sale_id):
    """
    Args:
        sale_id: ID of the sale to view
    """
    try:
        # Get the sale
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

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

#Opens up page as PDF
@method_decorator(login_required, name='dispatch')
class ReceiptPDFView(View):
    def get(self, request, *args, **kwargs):
        sale_id = kwargs.get('sale_id')
        try:
            # Get the sale
            sale = Sale.objects.get(id=sale_id)

            # Get the sale details
            details = SaleDetail.objects.filter(sale=sale)

            # Get the sale details with vat_rate=general and vat_rate=ZERO
            general_details = SaleDetail.objects.filter(sale=sale, product__vat_rate='GENERAL')
            zero_details = SaleDetail.objects.filter(sale=sale, product__vat_rate='ZERO')

            # Calculate the grand total for general_details
            general_grand_total = general_details.aggregate(sum_total=models.Sum('total_detail'))['sum_total'] or 0

            # Calculate the grand total for zero_details
            zero_grand_total = zero_details.aggregate(sum_total=models.Sum('total_detail'))['sum_total'] or 0


            # Get the logged-in username
            served_by = request.user.username

            # VAT analysis
            general_vat_rate = float(Tax.objects.get(slug='tax').percentage)
            general_vatable_amt = float(general_grand_total * ((100 - general_vat_rate) / 100))
            general_vat_amt = float(general_grand_total * (general_vat_rate/100))

            zero_vat_rate = float(0)
            zero_vatable_amt = float(zero_grand_total)
            zero_vat_amt = float(0)

            tax_instance = Tax.objects.get(slug='tax')

            # Define the dynamic data for the PDF template
            context = {
                "general_vat_rate":general_vat_rate,
                "zero_vat_rate":zero_vat_rate,
                "general_vatable_amt":general_vatable_amt,
                "general_vat_amt":general_vat_amt,
                "zero_vatable_amt":zero_vatable_amt,
                "zero_vat_amt":zero_vat_amt,
                "sale": sale,
                "general_details": general_details,
                "zero_details":zero_details,
                "details": details,
                "served_by": served_by,
                "tax_instance":tax_instance,
            }

            # Render the PDF using the dynamic data
            template = get_template('sales/sales_receipt_pdf.html')
            html = template.render(context)

            # CSS Boostrap
            css_url = os.path.join(
                settings.BASE_DIR, 'static/css/receipt_pdf/bootstrap.min.css')

            result = BytesIO()
            pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)

            if not pdf.err:
                return HttpResponse(result.getvalue(), content_type='application/pdf')
        except Sale.DoesNotExist:
            pass  # Handle the case where the sale with the given ID doesn't exist

        return HttpResponse("Error generating PDF", status=500)

@login_required(login_url="/accounts/login/")
def display_and_edit_tax(request):
    tax = get_object_or_404(Tax, slug='tax')
    tax_instance = Tax.objects.get(slug='tax')

    if request.method == 'POST':
        form = TaxForm(request.POST, instance=tax)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tax information updated successfully.',  extra_tags="success")
            return redirect('sales:display_and_edit_tax')
        else:
            messages.error(request, 'Error updating tax information. Please check the form.',  extra_tags="danger")

    else:
        form = TaxForm(instance=tax)

    return render(request, 'sales/tax.html', {'tax': tax, 'tax_instance':tax_instance, 'form': form})
