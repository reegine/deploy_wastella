# Generated by Django 5.1.5 on 2025-04-16 03:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0048_alter_voucher_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='voucher',
            name='category',
            field=models.CharField(choices=[('Entertainment', 'Entertainment'), ('F&B', 'Food & Beverage'), ('Shopping', 'Shopping'), ('Travel', 'Travel')], max_length=20),
        ),
    ]
