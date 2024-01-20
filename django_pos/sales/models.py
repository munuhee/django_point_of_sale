from django.db import models
from django.db.models import Sum, F, ExpressionWrapper, fields
import django.utils.timezone
from django.dispatch import receiver
from django.db.models.signals import post_save
from customers.models import Customer
from products.models import Product

class SaleManager(models.Manager):
    def get_total_sales_in_date_range(self, start_date, end_date):
        return self.filter(date_added__range=[start_date, end_date]).aggregate(sum_total=Sum('grand_total'))['sum_total'] or 0

    def get_total_profit_in_date_range(self, start_date, end_date):
        total_profit = self.filter(
            date_added__range=[start_date, end_date]
        ).aggregate(
            sum_total_profit=Sum('sale_profit')
        )['sum_total_profit'] or 0
        return total_profit

    def get_top_selling_products(self, start_date, end_date, num_products=3):
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
    sale_profit = models.FloatField(default=0)

    class Meta:
        db_table = 'Sales'

    def __str__(self) -> str:
        return "Sale ID: " + str(self.id) + " | Grand Total: " + str(self.grand_total) + " | Datetime: " + str(self.date_added)

    def sum_items(self):
        details = SaleDetail.objects.filter(sale=self.id)
        return sum([d.quantity for d in details])

    objects = SaleManager()

    def calculate_sale_profit(self):
        details = SaleDetail.objects.filter(sale=self)
        profit = sum([
            (detail.price - detail.product.buying_price) * detail.quantity
            if detail.price is not None and detail.product.buying_price is not None
            else 0
            for detail in details
        ])
        return profit

    def save(self, *args, **kwargs):
        self.sale_profit = self.calculate_sale_profit()
        super().save(*args, **kwargs)

class SaleDetail(models.Model):
    sale = models.ForeignKey(
        Sale, models.CASCADE, db_column='sale', related_name='saledetail_set')
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
    VAT_STATUS = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive")
    )
    percentage = models.DecimalField(max_digits=5, decimal_places=2, unique=True)
    slug = models.SlugField(unique=True, editable=True)
    status = models.CharField(
        choices=VAT_STATUS,
        max_length=100,
        default="INACTIVE",
        verbose_name="VAT status",
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f'tax-{self.id}')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Tax: {self.percentage}%'


@receiver(post_save, sender=SaleDetail)
def update_sale_profit(sender, instance, **kwargs):
    instance.sale.sale_profit = instance.sale.calculate_sale_profit()
    instance.sale.save()
