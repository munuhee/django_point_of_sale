from django.db import models
import django.utils.timezone
from django.db.models import Sum
from customers.models import Customer
from products.models import Product

class SaleManager(models.Manager):
    def get_total_sales_in_date_range(self, start_date, end_date):
        return self.filter(date_added__range=[start_date, end_date]).aggregate(sum_total=Sum('grand_total'))['sum_total'] or 0

    def get_top_selling_products(self, start_date, end_date, num_products=3):
        # Get the top-selling products within the date range
        top_products = SaleDetail.objects.filter(
            sale__date_added__range=[start_date, end_date]
        ).values('product__id', 'product__name').annotate(
            total_quantity=Sum('quantity')
        ).order_by('-total_quantity')[:num_products]

        return top_products

class Sale(models.Model):
    date_added = models.DateTimeField(default=django.utils.timezone.now)
    customer = models.ForeignKey(
        Customer, models.DO_NOTHING, db_column='customer')
    sub_total = models.FloatField(default=0)
    grand_total = models.FloatField(default=0)
    discount_amount = models.FloatField(default=0)
    discount_percentage = models.FloatField(default=0)
    amount_payed = models.FloatField(default=0)
    amount_change = models.FloatField(default=0)

    class Meta:
        db_table = 'Sales'

    def __str__(self) -> str:
        return "Sale ID: " + str(self.id) + " | Grand Total: " + str(self.grand_total) + " | Datetime: " + str(self.date_added)

    def sum_items(self):
        details = SaleDetail.objects.filter(sale=self.id)
        return sum([d.quantity for d in details])

    objects = SaleManager()


class SaleDetail(models.Model):
    sale = models.ForeignKey(
        Sale, models.DO_NOTHING, db_column='sale')
    product = models.ForeignKey(
        Product, models.DO_NOTHING, db_column='product')
    price = models.FloatField()
    quantity = models.IntegerField()
    total_detail = models.FloatField()

    class Meta:
        db_table = 'SaleDetails'

    def __str__(self) -> str:
        return "Detail ID: " + str(self.id) + " Sale ID: " + str(self.sale.id) + " Quantity: " + str(self.quantity)

class Tax(models.Model):
    percentage = models.DecimalField(max_digits=5, decimal_places=2, unique=True)

    def __str__(self):
        return f'Tax: {self.percentage}%'
