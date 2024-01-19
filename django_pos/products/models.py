from django.db import models
from django.forms import model_to_dict


class Category(models.Model):
    STATUS_CHOICES = (  # new
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive")
    )

    name = models.CharField(max_length=256)
    description = models.TextField(max_length=256)
    status = models.CharField(
        choices=STATUS_CHOICES,
        max_length=100,
        verbose_name="Status of the category",
    )

    class Meta:
        # Table's name
        db_table = "Category"
        verbose_name_plural = "Categories"

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    STATUS_CHOICES = (  # new
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive")
    )
    VAT_CHOICES = (
        ("GENERAL", "General"),
        ("ZERO", "Zero")
    )


    name = models.CharField(max_length=256)
    description = models.TextField(max_length=256)
    status = models.CharField(
        choices=STATUS_CHOICES,
        max_length=100,
        verbose_name="Status of the product",
    )
    category = models.ForeignKey(
        Category,
        related_name="products",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    price = models.FloatField(default=0)
    buying_price = models.FloatField(default=0)
    quantity = models.IntegerField(default=0)
    vat_rate = models.CharField(
        choices=VAT_CHOICES,
        default="GENERAL",
        max_length=100,
        verbose_name="VAT rates",
    )

    class Meta:
        # Table's name
        db_table = "Product"

    def __str__(self) -> str:
        return self.name

    def calculate_profit(self):
        return self.quantity * (self.price - self.buying_price)

    def to_json(self):
        item = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'category': self.category.name if self.category else None,
            'price': self.price,
            'buying_price': self.buying_price,
            'quantity': self.quantity,
            'vat_rate': self.vat_rate,
            'total_product': self.quantity * self.price,
            'profit': self.calculate_profit(),
        }
        return item
