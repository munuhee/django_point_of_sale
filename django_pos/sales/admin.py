from django.contrib import admin

from .models import Sale, SaleDetail, Tax

admin.site.register(Sale)
admin.site.register(SaleDetail)
admin.site.register(Tax)