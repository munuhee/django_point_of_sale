# Generated by Django 4.1.5 on 2024-01-14 21:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='loyalty_points',
            field=models.IntegerField(default=0),
        ),
    ]
