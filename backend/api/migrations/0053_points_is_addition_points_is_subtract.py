# Generated by Django 5.1.5 on 2025-04-17 03:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0052_points'),
    ]

    operations = [
        migrations.AddField(
            model_name='points',
            name='is_addition',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='points',
            name='is_subtract',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
    ]
