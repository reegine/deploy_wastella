# Generated by Django 5.1.5 on 2025-04-14 11:18

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0033_user_total_watched_video'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='total_watched_video',
        ),
        migrations.AddField(
            model_name='missionlist',
            name='detail_type',
            field=models.CharField(blank=True, choices=[('video', 'Video'), ('donate', 'Donate'), ('leaderboard', 'Leaderboard')], max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='missionprogress',
            name='assigned_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.CreateModel(
            name='UserMissionDataDays',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_reset_at', models.DateTimeField(auto_now_add=True)),
                ('reset_date', models.DateTimeField()),
                ('total_videos_watched', models.IntegerField(default=0)),
                ('current_leaderboard_rank', models.IntegerField(default=0)),
                ('last_donate_date', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'User Mission Data (Daily)',
            },
        ),
        migrations.CreateModel(
            name='UserMissionDataWeeks',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_reset_at', models.DateTimeField(auto_now_add=True)),
                ('reset_date', models.DateTimeField()),
                ('total_videos_watched', models.IntegerField(default=0)),
                ('current_leaderboard_rank', models.IntegerField(default=0)),
                ('last_donate_date', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'User Mission Data (Weekly)',
            },
        ),
    ]
