# Generated by Django 5.1.6 on 2025-07-17 04:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_alter_product_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_out_of_stock_manual',
            field=models.BooleanField(default=False),
        ),
    ]
