# Generated by Django 5.1.5 on 2025-04-15 15:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0039_alter_leaderboard_rank'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='message',
            field=models.CharField(choices=[('Thank You For The Donation', 'Thank You For The Donation'), ('Payment Failed', 'Payment Failed'), ('Order Failed', 'Order Failed'), ('You Have Successfully Ordered a Product', 'You Have Successfully Ordered a Product'), ('You Have Successfully Withdrawn Your Money', 'You Have Successfully Withdrawn Your Money')], max_length=255),
        ),
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.CharField(choices=[('Donation', 'Donation'), ('Payment Failed', 'Payment Failed'), ('Order Failed', 'Order Failed'), ('Success Ordered A Product', 'Success Ordered A Product'), ('Successful Withdrawing', 'Successful Withdrawing')], max_length=50),
        ),
    ]
