# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, AchievementList, UserAchievement, Donation, UserMissionDataDays, UserMissionDataWeeks, Leaderboard
from django.db.models import F
from .models import *


@receiver(post_save, sender=User)
def create_user_mission_data(sender, instance, created, **kwargs):
    if created:
        try:
            if not instance.pk:
                print("Instance PK not ready yet.")
                return
            
            # Example: assuming you filter by user.id or email
            if instance.email:
                UserMissionDataDays.objects.get_or_create(user=instance)
                UserMissionDataWeeks.objects.get_or_create(user=instance)
                print(f"UserMissionDataDays created for user {instance.email}")
                print(f"UserMissionDataWeeks created for user {instance.email}")
        except Exception as e:
            print(f"Error in signal while creating mission data: {e}")

@receiver(post_save, sender=User )
def check_achievements(sender, instance, **kwargs):
    # Get all achievements
    achievements = AchievementList.objects.all()

    # Fetch the actual points value from the database
    user_points = User.objects.filter(id=instance.id).values('points').first()['points']

    for achievement in achievements:
        # Now perform the comparison
        if user_points >= achievement.minimal_points:
            # Check if the user already has this achievement
            if not UserAchievement.objects.filter(user=instance, achievement=achievement).exists():
                # Create a new UserAchievement
                UserAchievement.objects.create(user=instance, achievement=achievement)

@receiver(post_save, sender=Donation)
def update_mission_data_on_donation(sender, instance, created, **kwargs):
    """
    Automatically updates mission data when a donation is marked as successful
    """
    if instance.status == 'Success':
        # Update daily mission data
        daily_data = UserMissionDataDays.objects.filter(user=instance.user).first()
        if daily_data:
            daily_data.save()  # This will trigger the validation and auto-update
            
        # Update weekly mission data
        weekly_data = UserMissionDataWeeks.objects.filter(user=instance.user).first()
        if weekly_data:
            weekly_data.save()

@receiver(post_save, sender=Leaderboard)
def update_mission_data_on_leaderboard_change(sender, instance, created, **kwargs):
    """
    Automatically updates mission data when leaderboard changes
    """
    # Update daily mission data
    daily_data = UserMissionDataDays.objects.filter(user=instance.user).first()
    if daily_data:
        daily_data.save()
    
    # Update weekly mission data
    weekly_data = UserMissionDataWeeks.objects.filter(user=instance.user).first()
    if weekly_data:
        weekly_data.save()

@receiver(post_save, sender=Leaderboard)
def check_leaderboard_missions(sender, instance, created, **kwargs):
    """
    Check and update leaderboard missions whenever leaderboard changes
    """
    user = instance.user
    rank = instance.rank
    
    # Update daily leaderboard data
    daily_data, _ = UserMissionDataDays.objects.get_or_create(user=user)
    daily_data.current_leaderboard_rank = rank
    daily_data.save(update_fields=['current_leaderboard_rank'])
    
    # Update weekly leaderboard data
    weekly_data, _ = UserMissionDataWeeks.objects.get_or_create(user=user)
    weekly_data.current_leaderboard_rank = rank
    weekly_data.save(update_fields=['current_leaderboard_rank'])

@receiver(post_save, sender=Points)
def update_leaderboard_on_point_change(sender, instance, **kwargs):
    Leaderboard.update_leaderboard()


@receiver(post_save, sender=UserMissionDataDays)
def update_daily_mission_progress(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return
        
    print(f"Updating daily mission progress for user {instance.user.id}")
    
    # Use update() for progress updates
    MissionProgress.objects.filter(
        user=instance.user,
        mission_id__type='daily',
        mission_id__detail_type='video',
        status='Ongoing'
    ).update(
        mission_progress=instance.total_videos_watched
    )

     # Update donation mission progress
    MissionProgress.objects.filter(
        user=instance.user,
        mission_id__type='daily',
        mission_id__detail_type='donate',
        status='Ongoing'
    ).update(
        mission_progress=instance.total_donation_count
    )

    # Update leaderboard mission progress
    MissionProgress.objects.filter(
        user=instance.user,
        mission_id__type='daily',
        mission_id__detail_type='leaderboard',
        status='Ongoing'
    ).update(
        mission_progress=1 if instance.current_leaderboard_rank <= 20 else 0
    )
    
    # Handle completions in a separate query
    completed_missions = MissionProgress.objects.filter(
        user=instance.user,
        mission_id__type='daily',
        mission_id__detail_type='video',
        status='Ongoing',
        mission_progress__gte=F('mission_id__mission_target')
    )

    # Handle donation mission completions
    completed_donate_missions = MissionProgress.objects.filter(
        user=instance.user,
        mission_id__type='daily',
        mission_id__detail_type='donate',
        status='Ongoing',
        mission_progress__gte=F('mission_id__mission_target')
    )

     # Handle leaderboard mission completions
    completed_leaderboard_missions = MissionProgress.objects.filter(
        user=instance.user,
        mission_id__type='daily',
        mission_id__detail_type='leaderboard',
        status='Ongoing',
        mission_progress=1  # 1 means they're in top 20
    )
    
    for mission in completed_missions:
        mission.status = 'Completed'
        if not mission.processed:
            # Call reward_user directly without save()
            mission.reward_user()
            mission.processed = True
        # Save with update_fields to avoid signal recursion
        mission.save(update_fields=['status', 'processed'])

    # Process completed donation missions
    for mission in completed_donate_missions:
        mission.status = 'Completed'
        if not mission.processed:
            mission.reward_user()
            mission.processed = True
        mission.save(update_fields=['status', 'processed'])

        # Process completed leaderboard missions
    for mission in completed_leaderboard_missions:
        mission.status = 'Completed'
        if not mission.processed:
            mission.reward_user()
            mission.processed = True
        mission.save(update_fields=['status', 'processed'])


@receiver(post_save, sender=UserMissionDataWeeks)
def update_weekly_mission_progress(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return
        
    print(f"Updating weekly mission progress for user {instance.user.id}")
    
    MissionProgress.objects.filter(
        user=instance.user,
        mission_id__type='weekly',
        mission_id__detail_type='video',
        status='Ongoing'
    ).update(
        mission_progress=instance.total_videos_watched
    )

     # Update donation mission progress
    MissionProgress.objects.filter(
        user=instance.user,
        mission_id__type='weekly',
        mission_id__detail_type='donate',
        status='Ongoing'
    ).update(
        mission_progress=instance.total_donation_count
    )

    # Update leaderboard mission progress
    MissionProgress.objects.filter(
        user=instance.user,
        mission_id__type='weekly',
        mission_id__detail_type='leaderboard',
        status='Ongoing'
    ).update(
        mission_progress=1 if instance.current_leaderboard_rank <= 20 else 0
    )
    
    completed_missions = MissionProgress.objects.filter(
        user=instance.user,
        mission_id__type='weekly',
        mission_id__detail_type='video',
        status='Ongoing',
        mission_progress__gte=F('mission_id__mission_target')
    )

    # Handle donation mission completions
    completed_donate_missions = MissionProgress.objects.filter(
        user=instance.user,
        mission_id__type='weekly',
        mission_id__detail_type='donate',
        status='Ongoing',
        mission_progress__gte=F('mission_id__mission_target')
    )

    # Handle leaderboard mission completions
    completed_leaderboard_missions = MissionProgress.objects.filter(
        user=instance.user,
        mission_id__type='weekly',
        mission_id__detail_type='leaderboard',
        status='Ongoing',
        mission_progress=1  # 1 means they're in top 20
    )
    
    for mission in completed_missions:
        mission.status = 'Completed'
        if not mission.processed:
            mission.reward_user()
            mission.processed = True
        mission.save(update_fields=['status', 'processed'])

    # Process completed donation missions
    for mission in completed_donate_missions:
        mission.status = 'Completed'
        if not mission.processed:
            mission.reward_user()
            mission.processed = True
        mission.save(update_fields=['status', 'processed'])

    # Process completed leaderboard missions
    for mission in completed_leaderboard_missions:
        mission.status = 'Completed'
        if not mission.processed:
            mission.reward_user()
            mission.processed = True
        mission.save(update_fields=['status', 'processed'])