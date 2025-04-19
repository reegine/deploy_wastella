from celery import Celery
from celery.schedules import crontab  # For scheduling tasks
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Import tasks here to avoid circular imports
    from api.tasks import (
        update_user_levels, 
        update_failed_donations,
        reset_daily_mission_progress,
        reset_weekly_mission_progress,
        reset_daily_missions,
        reset_weekly_missions,
        update_mission_progress,  # Import the new task
        expire_user_points,
    )

    # Calls update_user_levels every hour
    sender.add_periodic_task(
        crontab(minute=0, hour='*'),  # Every hour
        update_user_levels.s(),
        name='Update user levels every hour'
    )

    sender.add_periodic_task(
        crontab(minute=59, hour=23, day_of_month=31, month_of_year=12),  # Every 31st Dec at 11:59 PM
        expire_user_points.s(),
        name='Expire user points at the end of the year'
    )

    # Calls update_failed_donations every minute
    sender.add_periodic_task(60.0, update_failed_donations.s(), name='update failed donations every minute')

    # Calls update_mission_progress every 10 seconds
    sender.add_periodic_task(10.0, update_mission_progress.s(), name='Update mission progress every 10 seconds')

    # Reset daily mission progress and processed status every day at midnight
    sender.add_periodic_task(
        crontab(hour=0, minute=0),  # Daily at midnight
        reset_daily_mission_progress.s(),
        name='Reset daily mission progress'
    )
    sender.add_periodic_task(
        crontab(hour=0, minute=0),  # Daily at midnight
        reset_daily_missions.s(),
        name='Reset daily missions data'
    )

    # Reset weekly mission progress and processed status every Sunday at midnight
    sender.add_periodic_task(
        crontab(day_of_week=0, hour=0, minute=0),  # Weekly on Sunday at midnight
        reset_weekly_mission_progress.s(),
        name='Reset weekly mission progress'
    )
    sender.add_periodic_task(
        crontab(day_of_week=0, hour=0, minute=0),  # Weekly on Sunday at midnight
        reset_weekly_missions.s(),
        name='Reset weekly missions data'
    )

