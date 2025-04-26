from celery import shared_task
from django.core.management import call_command
from django.utils import timezone
from .models import *
from django.utils.timezone import now, datetime


@shared_task
def update_leaderboard_task():
    call_command('update_leaderboard')

@shared_task
def update_failed_donations():
    # Get the current time
    now = timezone.now()
    # Update donations that are still pending and have a due date that has passed
    Donation.objects.filter(status='pending', due_date__lt=now).update(status='failed')

@shared_task
def reset_daily_missions():
    """Reset daily mission data and progress."""
    print("Resetting daily missions...")
    
    # Reset mission data
    UserMissionDataDays.objects.all().update(
        total_videos_watched=0,
        total_donation_count=0,
        last_reset_at=timezone.now(),
        reset_date=timezone.now() + timedelta(days=1)
    )
    
    # Reset mission progress
    MissionProgress.objects.filter(mission_id__type='daily').update(
        mission_progress=0,
        status='Ongoing',
        processed=False
    )


@shared_task
def reset_weekly_missions():
    """Reset weekly mission data and progress."""
    print("Resetting weekly missions...")
    
    # Reset mission data
    UserMissionDataWeeks.objects.all().update(
        total_videos_watched=0,
        total_donation_count=0,
        last_reset_at=timezone.now(),
        reset_date=timezone.now() + timedelta(weeks=1)
    )
    
    # Reset mission progress
    MissionProgress.objects.filter(mission_id__type='weekly').update(
        mission_progress=0,
        status='Ongoing',
        processed=False
    )

@shared_task
def reset_daily_mission_progress():
    """Reset daily mission progress and processed status."""
    for progress in MissionProgress.objects.filter(mission_id__type='daily'):
        progress.mission_progress = 0
        progress.processed = False
        progress.status = 'Ongoing'
        progress.save()


@shared_task
def reset_weekly_mission_progress():
    """Reset weekly mission progress and processed status."""
    for progress in MissionProgress.objects.filter(mission_id__type='weekly'):
        progress.mission_progress = 0
        progress.processed = False
        progress.status = 'Ongoing'
        progress.save()

# @shared_task
# def update_mission_progress():
#     """Update mission progress for all ongoing missions."""
#     print("Executing update_mission_progress task...")  # Debug log
#     mission_progresses = MissionProgress.objects.filter(status='Ongoing')

#     for progress in mission_progresses:
#         print(f"Updating mission progress for user: {progress.user.username}, mission: {progress.mission_id.id}")
        
#         if progress.mission_id.type == 'daily':
#             daily_data = UserMissionDataDays.objects.filter(user=progress.user).first()
#             if daily_data:
#                 progress.mission_progress = progress.get_progress_based_on_detail_type(daily_data)
#         elif progress.mission_id.type == 'weekly':
#             weekly_data = UserMissionDataWeeks.objects.filter(user=progress.user).first()
#             if weekly_data:
#                 progress.mission_progress = progress.get_progress_based_on_detail_type(weekly_data)
        
#         # Save the updated progress
#         progress.save()

@shared_task
def update_mission_progress():
    """Update and evaluate all mission progress."""
    print("Starting mission progress update...")
    
    # Process all ongoing missions
    for progress in MissionProgress.objects.filter(status='Ongoing'):
        try:
            progress.save()  # This will trigger evaluation and rewards
        except Exception as e:
            print(f"Error updating mission {progress.id}: {e}")


@shared_task
def update_user_levels():
    """Periodically update user levels based on total_xp."""
    users = User.objects.all()
    for user in users:
        if 0 <= user.total_xp < 100:
            new_level = "Level 1"
        elif 100 <= user.total_xp < 200:
            new_level = "Level 2"
        elif 200 <= user.total_xp < 300:
            new_level = "Level 3"
        elif 300 <= user.total_xp < 400:
            new_level = "Level 4"
        elif 400 <= user.total_xp <= 500:
            new_level = "Level 5"
        else:
            new_level = user.level  # Keep the current level if no change

        if user.level != new_level:
            user.level = new_level
            user.save()

@shared_task
def expire_user_points():
    """
    Task to expire all user points at the end of the year.
    """
    current_year = now().year
    expiration_date = now().replace(year=current_year, month=12, day=31, hour=23, minute=59, second=59)
    
    if now() >= expiration_date:
        # Expire points for all users
        users = User.objects.filter(points__gt=0)
        for user in users:
            user.expire_points()