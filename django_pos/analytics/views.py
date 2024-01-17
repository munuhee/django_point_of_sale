from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum
from django.utils.dateparse import parse_datetime
from sales.models import Sale

def analytics_view(request):
    """
    View function for handling analytics requests.

    This function retrieves the date range from the POST request and calculates
    the total sales for the specified period. The result is returned as a JSON response.

    Parameters:
    - request (HttpRequest): The HTTP request object.

    Returns:
    - JsonResponse: A JSON response containing the total sales for the specified date range.
    - HttpResponse: The rendered analytics template if the request method is not POST.
    """
    if request.method == 'POST':
        print('Received POST request')
        print(request.POST)
        date_range = request.POST.get('date_range')

        if date_range == 'today':
            now = timezone.now()
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif date_range == 'last_week':
            end_date = timezone.now()
            start_date = end_date - timezone.timedelta(days=end_date.weekday() + 7)
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif date_range == 'last_30_days':
            end_date = timezone.now()
            start_date = end_date - timezone.timedelta(days=30)
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif date_range == 'custom':
            start_date = parse_datetime(request.POST.get('start_date'))
            end_date = parse_datetime(request.POST.get('end_date'))
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        query = {'date_added__range': [start_date, end_date]}
        print(Sale.objects.filter(**query).query)  # Check the generated query
        total_sales = Sale.objects.filter(**query).aggregate(sum_total=Sum('grand_total'))['sum_total'] or 0
        total_sales = round(total_sales, 2)

        # Get the top 3 selling products
        top_selling_products = Sale.objects.get_top_selling_products(start_date, end_date, num_products=3)

        # Prepare the response data
        response_data = {
            'total_sales': total_sales,
            'top_selling_products': list(top_selling_products),
        }

        return JsonResponse(response_data)
    else:
        return render(request, 'analytics/analytics_template.html', {"active_icon": "analytics"})
