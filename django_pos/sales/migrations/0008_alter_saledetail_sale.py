# Generated by Django 4.1.5 on 2024-01-19 14:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0007_sale_sale_profit_alter_saledetail_sale'),
    ]

    operations = [
        migrations.AlterField(
            model_name='saledetail',
            name='sale',
            field=models.ForeignKey(db_column='sale', on_delete=django.db.models.deletion.CASCADE, related_name='saledetail_set', to='sales.sale'),
        ),
    ]
