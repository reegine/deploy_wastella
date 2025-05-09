# Generated by Django 5.1.5 on 2025-04-15 16:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0040_alter_notification_message_alter_notification_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wastecollection',
            name='is_approved',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name='wastecollection',
            name='processing_facility',
            field=models.CharField(blank=True, choices=[('recycling_plant', 'Recycling Plant'), ('biogas_facility', 'Biogas Facility'), ('landfill', 'Landfill'), ('other', 'Other')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='wastecollection',
            name='usage_before_disposal',
            field=models.CharField(blank=True, choices=[('single_use', 'Single Use'), ('reused', 'Reused'), ('repurposed', 'Repurposed')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='wastecollection',
            name='wastes',
            field=models.ManyToManyField(blank=True, null=True, related_name='waste_collections', to='api.waste'),
        ),
    ]
