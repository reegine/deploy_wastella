# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, AchievementList, UserAchievement, Donation, UserMissionDataDays, UserMissionDataWeeks, Leaderboard
from django.db.models import F


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