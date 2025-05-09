# Generated by Django 5.1.5 on 2025-03-21 05:12

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrashEducation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('media_url', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='WasteBank',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('latitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('longitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('address', models.TextField()),
                ('operational_hours', models.CharField(max_length=255)),
                ('accepted_waste_types', models.TextField()),
                ('service_type', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('username', models.CharField(max_length=255, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('password', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('profile_picture', models.CharField(blank=True, max_length=255, null=True)),
                ('isSeller', models.BooleanField(default=False)),
                ('gender', models.CharField(choices=[('Woman', 'Woman'), ('Man', 'Man'), ('Prefer Not To Say', 'Prefer Not To Say')], default='Prefer Not To Say', max_length=20)),
                ('level', models.CharField(choices=[('Level 1', 'Level 1'), ('Level 2', 'Level 2'), ('Level 3', 'Level 3'), ('Level 4', 'Level 4'), ('Level 5', 'Level 5'), ('Level 6', 'Level 6')], default='Level 1', max_length=10)),
                ('store_name', models.CharField(blank=True, max_length=255, null=True)),
                ('phone_number', models.IntegerField(blank=True, null=True)),
                ('store_address', models.CharField(blank=True, max_length=255, null=True)),
                ('id_card_photo', models.FileField(blank=True, null=True, upload_to='id_cards/')),
                ('virtual_account', models.CharField(blank=True, max_length=255, null=True)),
                ('virtual_account_name', models.CharField(blank=True, max_length=255, null=True)),
                ('bank_issuer', models.CharField(blank=True, choices=[('BCA', 'BCA')], max_length=10, null=True)),
                ('total_product', models.IntegerField(default=0)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_superuser', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('phone_number', models.IntegerField()),
                ('street_address', models.CharField(max_length=255)),
                ('city', models.CharField(max_length=255)),
                ('postal_code', models.CharField(max_length=20)),
                ('province', models.CharField(max_length=255)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='OTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('otp', models.CharField(max_length=6)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('total_rating', models.DecimalField(decimal_places=2, default=0.0, max_digits=3)),
                ('compostable', models.BooleanField()),
                ('nontoxic', models.BooleanField()),
                ('breathable', models.BooleanField()),
                ('price', models.FloatField()),
                ('image', models.FileField(upload_to='products/')),
                ('stock', models.IntegerField()),
                ('category', models.CharField(choices=[('Personal Care', 'Personal Care'), ('Green Tech & Gadget', 'Green Tech & Gadget'), ('Sustainable Products', 'Sustainable Products'), ('Eco-Friendly Home', 'Eco-Friendly Home'), ('Green Stationary', 'Green Stationary'), ('Eco-Friendly Fashion', 'Eco-Friendly Fashion')], max_length=50)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('city', models.CharField(default='Jakarta', max_length=255)),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('delivery_shipping_id', models.CharField(max_length=255)),
                ('virtual_account', models.CharField(max_length=255)),
                ('message', models.TextField(blank=True, null=True)),
                ('status', models.CharField(choices=[('On Delivery', 'On Delivery'), ('Canceled', 'Canceled'), ('Success', 'Success')], max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('address', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.address')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('review_text', models.TextField()),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('review_star', models.DecimalField(decimal_places=1, default=0.0, max_digits=2)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SustainabilityImpact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_tree', models.IntegerField()),
                ('total_recycled', models.IntegerField()),
                ('total_carbon', models.IntegerField()),
                ('total_co2', models.IntegerField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
