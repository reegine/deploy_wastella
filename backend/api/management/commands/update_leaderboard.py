from django.core.management.base import BaseCommand
from your_app.models import Leaderboard, User
from django.db.models import F, Window
from django.db.models.functions import Rank

class Command(BaseCommand):
    help = 'Updates the leaderboard ranks based on user points'

    def handle(self, *args, **kwargs):
        # Step 1: Calculate ranks for all users
        users = User.objects.annotate(
            rank=Window(
                expression=Rank(),
                order_by=F('points').desc()
            )
        ).values('id', 'points', 'rank')

        # Step 2: Update or create Leaderboard entries
        for user in users:
            Leaderboard.objects.update_or_create(
                user_id=user['id'],
                defaults={'user_points': user['points'], 'rank': user['rank']}
            )

        # Step 3: Print a success message
        self.stdout.write(self.style.SUCCESS('Successfully updated leaderboard ranks'))