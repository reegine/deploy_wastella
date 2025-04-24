from django.db import models, IntegrityError
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg
from django.db.models import F, Window
from django.db.models.functions import Rank
from django.core.exceptions import ValidationError
from django.utils.timezone import now

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username field must be set")
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, email, password, **extra_fields)

class User(AbstractBaseUser , PermissionsMixin):
    GENDER_CHOICES = [
        ("Woman", "Woman"),
        ("Man", "Man"),
        ("Prefer Not To Say", "Prefer Not To Say")
    ]
    LEVEL_CHOICES = [(f"Level {i}", f"Level {i}") for i in range(1, 6)]  # Levels 1 to 5
    BANK_CHOICES = [
        ("BCA", "BCA"),
        ("Mandiri", "Mandiri"),
        ("BRI", "BRI")
    ]
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)
    profile_picture = models.FileField(upload_to='profile-pic/', blank=True, null=True)
    isSeller = models.BooleanField(default=False)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default="Prefer Not To Say")
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default="Level 1")
    store_name = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True) 
    store_address = models.CharField(max_length=255, blank=True, null=True)
    id_card_photo = models.FileField(upload_to='id_cards/', blank=True, null=True)
    virtual_account = models.CharField(max_length=255, blank=True, null=True)
    virtual_account_name = models.CharField(max_length=255, blank=True, null=True)
    bank_issuer = models.CharField(max_length=10, choices=BANK_CHOICES, blank=True, null=True)
    total_product = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    total_donations = models.IntegerField(default=0)
    total_xp = models.IntegerField(default=0)
    total_balance = models.IntegerField(default=0, blank=True, null=True)

    # Add is_staff and is_superuser fields
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UserManager()
    USERNAME_FIELD = 'username'  # Use username as the primary identifier
    REQUIRED_FIELDS = ['email']  # Add username to required fields

    def save(self, *args, **kwargs):
        is_new = self._state.adding  # Check if this is a new user
        
        # super().save(*args, **kwargs)  # Save the user first
        
        # if is_new:
        #     try:
        #         print(f"Creating mission data for new user: {self}")
        #         UserMissionDataDays.create_for_user(self)
        #         UserMissionDataWeeks.create_for_user(self)
        #         Leaderboard.update_leaderboard()
        #     except Exception as e:
        #         print(f"Error in creating related data during user creation: {e}")
        
        # Automatically update the user's level based on total_xp
        try:
            if 0 <= self.total_xp < 100:
                self.level = "Level 1"
            elif 100 <= self.total_xp < 200:
                self.level = "Level 2"
            elif 200 <= self.total_xp < 300:
                self.level = "Level 3"
            elif 300 <= self.total_xp < 400:
                self.level = "Level 4"
            elif 400 <= self.total_xp <= 500:
                self.level = "Level 5"
        except Exception as e:
            print(f"Error in updating user level: {e}")

        Leaderboard.update_leaderboard()

        super().save(*args, **kwargs)  # Save the user again

    # Methods for manual addition and subtraction of points
    def add_points(self, amount, reason=None):
        """
        Add points to the user and create a Points entry.
        """
        if amount <= 0:
            raise ValidationError("Points to be added must be greater than 0.")

        Points.objects.create(user=self, amount=amount, reason=reason, is_subtract=False, is_addition=True)
        self.points = F('points') + amount
        self.save()
        self.refresh_from_db()
        Leaderboard.update_leaderboard()

    def subtract_points(self, amount, reason=None):
        """
        Subtract points from the user and create a Points entry.
        """
        if amount <= 0:
            raise ValidationError("Points to be subtracted must be greater than 0.")
        if self.points < amount:
            raise ValidationError("User does not have enough points to subtract.")

        Points.objects.create(user=self, amount=-amount, reason=reason, is_subtract=True, is_addition=False)
        self.points = F('points') - amount
        self.save()
        self.refresh_from_db()
        Leaderboard.update_leaderboard()

    def expire_points(self):
        """
        Expire all remaining points for the user at the end of the year.
        """
        if self.points > 0:
            # Create an entry in the PointsExpire model
            PointsExpire.objects.create(user=self, expired_points=self.points)
            # Reset the user's points to zero
            self.points = 0
            self.save()


class Points(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='points_history')
    amount = models.IntegerField()  # Positive for added points, negative for subtracted points
    added_at = models.DateTimeField(auto_now_add=True)
    # expires_at = models.DateTimeField(blank=True, null=True)
    reason = models.CharField(max_length=255, blank=True, null=True)  # Optional reason for the points change
    is_subtract = models.BooleanField()
    is_addition = models.BooleanField()

    def save(self, *args, **kwargs):
        # Set added_at to now if it is None
        if self.added_at is None:
            self.added_at = timezone.now()

        # Automatically set expiration date to 3 months after added_at
        if not self.expires_at:
            self.expires_at = self.added_at + timedelta(days=90)

        # Ensure points are synchronized with the User model
        if not self.pk:  # Only adjust User points if this is a new entry
            self.update_user_points()

        Leaderboard.update_leaderboard()

        super().save(*args, **kwargs)

    def update_user_points(self):
        """
        Add or subtract points from the associated user when a Points instance is created.
        """
        if self.amount:
            self.user.points = F('points') + self.amount
            self.user.save()
            self.user.refresh_from_db()  # Refresh the user instance to update fields

        Leaderboard.update_leaderboard()

    # @classmethod
    # def remove_expired_points(cls):
    #     """
    #     Automatically handle expired points by subtracting from the user's balance.
    #     """
    #     expired_points = cls.objects.filter(expires_at__lte=timezone.now(), amount__gt=0)
    #     for point in expired_points:
    #         # Subtract expired points from the user's balance
    #         point.user.points = F('points') - point.amount
    #         point.user.save()
    #         point.user.refresh_from_db()  # Refresh the user instance

    #         # Delete the expired point entry
    #         point.delete()

    def __str__(self):
        return f"{self.user.username} - {self.amount} points (Added: {self.added_at}, Expires: {self.expires_at})"

class PointsExpire(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='points_expire_history')
    expired_points = models.IntegerField()  # Number of points that expired
    expired_at = models.DateTimeField(auto_now_add=True)  # When the points expired

    def __str__(self):
        return f"{self.user.username} - {self.expired_points} points expired at {self.expired_at}"

class Address(models.Model):
    # id = models.CharField(max_length=255, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    province = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.user} - {self.street_address}"

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        # Set OTP expiration to 10 minutes from creation
        self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

class SustainabilityImpact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_tree = models.IntegerField()
    total_recycled = models.IntegerField()
    total_carbon = models.IntegerField()
    total_co2 = models.IntegerField()

class Product(models.Model):
    CATEGORY_CHOICES = [
        # ('Personal Care', 'Personal Care'),
        ('Green Tech & Gadget', 'Green Tech & Gadget'),
        ('Sustainable Living', 'Sustainable Living'),
        ('Eco-Friendly Home', 'Eco-Friendly Home'),
        # ('Green Stationary', 'Green Stationary'),
        ('Eco-Friendly Fashion', 'Eco-Friendly Fashion')
    ]
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    total_rating = models.DecimalField(default=0.0, max_digits=3, decimal_places=2, editable=False)  # Make total_rating read-only
    compostable = models.BooleanField()
    nontoxic = models.BooleanField()
    breathable = models.BooleanField()
    price = models.FloatField()
    image = models.FileField(upload_to='products/')
    stock = models.IntegerField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    @property
    def city(self):
        # Get the seller's primary address (or any address) and return the city
        seller_address = self.seller.address_set.first()  # Get the first address of the seller
        return seller_address.city if seller_address else "Unknown"

    def update_total_rating(self):
        # Calculate the average rating from all reviews for this product
        avg_rating = self.review_set.aggregate(Avg('review_star'))['review_star__avg']
        self.total_rating = avg_rating if avg_rating is not None else 0.0
        self.save()

    def save(self, *args, **kwargs):
        # Check if this is a new product (i.e., it doesn't have an ID yet)
        is_new = self._state.adding

        # Save the product first
        super().save(*args, **kwargs)

        # If this is a new product, increment the seller's total_product count
        if is_new:
            self.seller.total_product += 1
            self.seller.save()

    def delete(self, *args, **kwargs):
        # Decrement the seller's total_product count
        self.seller.total_product -= 1
        self.seller.save()

        # Delete the product
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.seller}"

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review_text = models.TextField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    review_star = models.DecimalField(default=0.0, max_digits=2, decimal_places=1)

    def save(self, *args, **kwargs):
        # Save the review first
        super().save(*args, **kwargs)

        # Update the product's total_rating
        self.product.update_total_rating()

    def delete(self, *args, **kwargs):
        # Delete the review
        super().delete(*args, **kwargs)

        # Update the product's total_rating
        self.product.update_total_rating()

class Shipping(models.Model):
    delivery_name = models.CharField(max_length=255)  # e.g., JNE, J&T
    delivery_price = models.FloatField()  # Delivery fee for this option

    def __str__(self):
        return f"{self.delivery_name} - {self.delivery_price}"


class Purchase(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Prepared By Seller', 'Prepared By Seller'),
        ('On Delivery', 'On Delivery'),
        ('Canceled', 'Canceled'),
        ('Success', 'Success')
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    shipping = models.ForeignKey(Shipping, on_delete=models.SET_NULL, null=True, blank=True) 
    delivery_fee = models.FloatField(default=0.0)  # Store the delivery fee
    virtual_account = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')  # Default to 'Pending'
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(blank=True, null=True)  # Add due_date field

    def save(self, *args, **kwargs):
        # Automatically set the virtual_account to the seller's virtual_account
        if not self.virtual_account:
            self.virtual_account = self.product.seller.virtual_account

        # Automatically set the delivery_fee based on the selected shipping option
        if self.shipping:
            self.delivery_fee = self.shipping.delivery_price

        super().save(*args, **kwargs)  # Save the object first

        # Set the due_date to 24 hours from created_at if it's not already set
        if not self.due_date:
            self.due_date = self.created_at + timedelta(hours=24)
            self.save()  # Save the object again to update the due_date

    @property
    def total_price(self):
        return self.product.price + self.delivery_fee

    def update_status(self, new_status):
        print(f"Updating status of Purchase ID {self.id} from {self.status} to {new_status}")

        # Create a notification for specific statuses
        if new_status == 'Prepared By Seller':
            print("Creating notification for 'Prepared By Seller'")
            Notification.objects.create(
                user=self.user,
                message='You Have Successfully Ordered a Product',
                type='Success Ordered A Product'
            )
        elif new_status == 'Canceled':
            print("Creating notification for 'Canceled'")
            Notification.objects.create(
                user=self.user,
                message='Order Failed',
                type='Order Failed'
            )

        # Update the purchase status
        if new_status == 'Success' and self.status != 'Success':
            # Update the seller's total balance
            self.product.seller.total_balance += self.total_price
            self.product.seller.save()

        self.status = new_status
        self.save()

class WasteBank(models.Model):
    # bank_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    address = models.TextField()
    operational_hours = models.CharField(max_length=255)
    accepted_waste_types = models.TextField()
    service_type = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name

    def get_maps_link(self):
        return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
class TrashEducation(models.Model):
    # education_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    media_url = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

# Trash Education Section

class WasteType(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name

class WasteImage(models.Model):
    waste = models.ForeignKey(WasteType, related_name="images", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to="waste_images/")  # Upload gambar langsung

    def __str__(self):
        return self.name

class Fact(models.Model):
    waste = models.ForeignKey(WasteType, related_name="facts", on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self):
        return self.text[:50]

class Myth(models.Model):
    waste = models.ForeignKey(WasteType, related_name="myths", on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self):
        return self.text[:50]

class ProcessingMethod(models.Model):
    waste = models.ForeignKey(WasteType, related_name="processing_methods", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.title


class MissionList(models.Model):
    MISSION_TYPE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ]
    MISSION_DETAIL_TYPE_CHOICES = [
        ('video', 'Video'),
        ('donate', 'Donate'),
        ('leaderboard', 'Leaderboard'),
    ]
    # id = models.CharField(max_length=255, primary_key=True)
    points = models.IntegerField()
    mission_description = models.CharField(max_length=255)
    mission_target = models.IntegerField()
    xp = models.IntegerField()
    type = models.CharField(max_length=10, choices=MISSION_TYPE_CHOICES)
    detail_type = models.CharField(max_length=50, choices=MISSION_DETAIL_TYPE_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"{self.mission_description}"

from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.db.models import F


class MissionProgress(models.Model):
    STATUS_CHOICES = [
        ('Ongoing', 'Ongoing'),
        ('Completed', 'Completed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mission_id = models.ForeignKey(MissionList, on_delete=models.CASCADE)
    mission_progress = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Ongoing')
    updated_at = models.DateTimeField(auto_now=True)
    assigned_at = models.DateTimeField(auto_now=True)
    processed = models.BooleanField(default=False)  # Tracks if points/XP have been added

    def save(self, *args, **kwargs):
        # Determine mission progress based on type and detail_type
        self.evaluate_progress()

        # Check if mission is completed
        if self.mission_progress >= self.mission_id.mission_target:
            self.status = 'Completed'

            # Add points and XP only if not already processed
            if not self.processed:
                self.add_points_and_xp()
                self.processed = True  # Mark as processed

        super().save(*args, **kwargs)

    def evaluate_progress(self):
        """Evaluate mission progress based on type and detail_type."""
        if self.mission_id.type == 'daily':
            daily_data = UserMissionDataDays.objects.filter(user=self.user).first()
            if daily_data:
                self.mission_progress = self.get_progress_based_on_detail_type(daily_data)
        elif self.mission_id.type == 'weekly':
            weekly_data = UserMissionDataWeeks.objects.filter(user=self.user).first()
            if weekly_data:
                self.mission_progress = self.get_progress_based_on_detail_type(weekly_data)

    def get_progress_based_on_detail_type(self, data):
        """Get mission progress based on the detail type."""
        if self.mission_id.detail_type == 'video':
            print(f"Calculating progress for video: {data.total_videos_watched}")
            return data.total_videos_watched
        elif self.mission_id.detail_type == 'donate':
            print(f"Calculating progress for donate: {data.total_donation_count}")
            return data.total_donation_count
        elif self.mission_id.detail_type == 'leaderboard':
            # Leaderboard missions are reversed; lower ranks are better
            progress = max(0, self.mission_id.mission_target - data.current_leaderboard_rank)
            print(f"Calculating progress for leaderboard: {progress}")
            return progress
        return 0

    def add_points_and_xp(self):
        # Subtract points from the user and create a Points entry
        Points.objects.create(
            user=self.user,
            amount=+self.mission_id.points,  # Negative points for redemption
            reason=f"You Completed A Mission!",
            is_addition=True,
            is_subtract=False,
        )
        """Add points and XP to the user."""
        # self.user.points = F('points') + self.mission_id.points
        self.user.total_xp = F('total_xp') + self.mission_id.xp
        self.user.save()
        self.user.refresh_from_db()  # Refresh the object to get updated values
        print(f"User {self.user.username} updated: Points={self.user.points}, XP={self.user.total_xp}")

class WasteWrap(models.Model):
    # id = models.CharField(max_length=255, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organic = models.IntegerField()
    inorganic = models.IntegerField()
    hazardous = models.IntegerField()
    residual = models.IntegerField()
    co_reduced = models.IntegerField()
    co_description = models.CharField(max_length=255)
    electricity_reduced = models.IntegerField()
    electricity_description = models.CharField(max_length=255)
    recycle_value = models.IntegerField()
    future_footprint = models.IntegerField()
    water_saved = models.IntegerField()
    water_saved_description = models.CharField(max_length=255)
    waste_efforts = models.IntegerField()

class Donation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    amount = models.IntegerField()
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Save the donation instance first
        super().save(*args, **kwargs)

        # Automatically set the due_date to 1 hour from created_at if it's not already set
        if not self.due_date:
            self.due_date = self.created_at + timedelta(hours=1)
            # Update only the due_date field
            self.__class__.objects.filter(id=self.id).update(due_date=self.due_date)

        
        print(f"Processing successful donation for user {self.user.id}")
        print(f"Donation created_at: {self.created_at}")

        if self.status.lower() == 'success':  # Ensure case-insensitivity
            # Update daily mission data
            daily_data, created = UserMissionDataDays.objects.get_or_create(
                user=self.user,
                defaults={'last_reset_at': timezone.now(), 'reset_date': timezone.now() + timedelta(days=1)}
            )
            print(f"Daily mission data: {daily_data}, created: {created}")
            donations = Donation.objects.filter(
                user=self.user,
                status__iexact='success',  # Case-insensitive comparison
                created_at__gte=daily_data.last_reset_at,
                created_at__lte=daily_data.reset_date
            )
            daily_data.total_donation_count = donations.count()
            daily_data.save()
            print(f"Updated total_donation_count for daily: {daily_data.total_donation_count}")

            # Update weekly mission data
            weekly_data, created = UserMissionDataWeeks.objects.get_or_create(
                user=self.user,
                defaults={'last_reset_at': timezone.now(), 'reset_date': timezone.now() + timedelta(weeks=1)}
            )
            print(f"Weekly mission data: {weekly_data}, created: {created}")
            donations = Donation.objects.filter(
                user=self.user,
                status__iexact='success',  # Case-insensitive comparison
                created_at__gte=weekly_data.last_reset_at,
                created_at__lte=weekly_data.reset_date
            )
            weekly_data.total_donation_count = donations.count()
            weekly_data.save()
            print(f"Updated total_donation_count for weekly: {weekly_data.total_donation_count}")

            # Add points to the user and create a Points entry
            Points.objects.create(
                user=self.user,
                amount=+1000,  # Points for donating
                reason=f"You Just Donated!",
                is_addition=True,
                is_subtract = False,
            )

class Leaderboard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_points = models.IntegerField()
    rank = models.IntegerField(unique=True)  # Make rank unique

    class Meta:
        ordering = ['rank']

    @classmethod
    def update_leaderboard(cls):
        # Get users with their points
        users = User.objects.values('id', 'points').order_by('-points')

        rank = 1
        for user in users:
            try:
                # Update or create leaderboard entry with a unique rank
                cls.objects.update_or_create(
                    user_id=user['id'],
                    defaults={'user_points': user['points'], 'rank': rank},
                )
                rank += 1
            except IntegrityError:
                # Handle a rare case where rank conflicts occur
                cls.resolve_rank_conflicts()
                cls.update_leaderboard()
                break

    @classmethod
    def resolve_rank_conflicts(cls):
        """
        Resolve rank conflicts by reassigning ranks to users in the correct order.
        """
        leaderboard_entries = cls.objects.order_by('rank', '-user_points')
        rank = 1
        for entry in leaderboard_entries:
            if entry.rank != rank:
                entry.rank = rank
                entry.save()
            rank += 1

class FAQ(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.CharField(max_length=255)
    answer = models.TextField(blank=True, null=True)
    answered_at = models.DateTimeField(blank=True, null=True)
    asked_at = models.DateTimeField(auto_now_add=True)

class AchievementList(models.Model):
    message = models.CharField(max_length=255)
    minimal_points = models.IntegerField()

class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(AchievementList, on_delete=models.CASCADE)

class ReelVideos(models.Model):
    video_url = models.CharField(max_length=255)
    video_id = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    short_description = models.CharField(max_length=255)

# class WasteCollection(models.Model):
#     WASTE_TYPE_CHOICES = [
#         ('organic', 'Organic'),
#         ('non_organic', 'Non Organic'),
#         ('hazardous', 'Hazardous'),
#         ('paper', 'Paper'),
#         ('residual', 'Residual')
#     ]
    
#     WASTE_CONDITION_CHOICES = [
#         ('clean', 'Clean'),
#         ('dirty', 'Dirty'),
#         ('mixed', 'Mixed')
#     ]
    
#     PROCESSING_FACILITY_CHOICES = [
#         ('recycling_plant', 'Recycling Plant'),
#         ('biogas_facility', 'Biogas Facility'),
#         ('landfill', 'Landfill'),
#         ('other', 'Other')
#     ]
    
#     USAGE_CHOICES = [
#         ('single_use', 'Single Use'),
#         ('reused', 'Reused'),
#         ('repurposed', 'Repurposed')
#     ]

#     # id = models.CharField(max_length=50, primary_key=True)
#     waste_weight = models.DecimalField(max_digits=10, decimal_places=2)
#     waste_type = models.CharField(max_length=20, choices=WASTE_TYPE_CHOICES)
#     waste_condition = models.CharField(max_length=20, choices=WASTE_CONDITION_CHOICES)
#     processing_facility = models.CharField(max_length=20, choices=PROCESSING_FACILITY_CHOICES)
#     usage_before_disposal = models.CharField(max_length=20, choices=USAGE_CHOICES)
#     user = models.ForeignKey(
#         User, 
#         on_delete=models.CASCADE, 
#         related_name='submitted_collections',
#         null=True,  # Allow NULL values
#         blank=True  # Allow blank values
#     )
#     admin = models.ForeignKey(
#         User, 
#         on_delete=models.SET_NULL, 
#         null=True, 
#         blank=True,
#         related_name='approved_collections'
#     )
#     # scanned_data = models.TextField(blank=True, null=True)
#     is_approved = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     approved_at = models.DateTimeField(null=True, blank=True)

#     class Meta:
#         ordering = ['-created_at']

#     def save(self, *args, **kwargs):
#         # Update approved_at timestamp when admin approves
#         if self.is_approved and not self.approved_at:
#             self.approved_at = timezone.now()
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"Waste Collection {self.id}"

class Waste(models.Model):
    WASTE_TYPE_CHOICES = [
        ('organic', 'Organic'),
        ('non_organic', 'Non Organic'),
        ('hazardous', 'Hazardous'),
        ('paper', 'Paper'),
        ('residual', 'Residual')
    ]
    
    WASTE_CONDITION_CHOICES = [
        ('clean', 'Clean'),
        ('dirty', 'Dirty'),
        ('mixed', 'Mixed')
    ]

    waste_weight = models.DecimalField(max_digits=10, decimal_places=2)
    waste_type = models.CharField(max_length=20, choices=WASTE_TYPE_CHOICES)
    waste_condition = models.CharField(max_length=20, choices=WASTE_CONDITION_CHOICES)

    def clean(self):
        if self.waste_weight <= 0:
            raise ValidationError("Waste weight must be greater than 0.")

    def __str__(self):
        return f"{self.waste_type} - {self.waste_weight}kg"

class WasteCollection(models.Model):
    PROCESSING_FACILITY_CHOICES = [
        ('recycling_plant', 'Recycling Plant'),
        ('biogas_facility', 'Biogas Facility'),
        ('landfill', 'Landfill'),
        ('other', 'Other')
    ]
    
    USAGE_CHOICES = [
        ('single_use', 'Single Use'),
        ('reused', 'Reused'),
        ('repurposed', 'Repurposed')
    ]

    wastes = models.ManyToManyField(Waste, related_name='waste_collections', blank=True)  # Allow blank
    processing_facility = models.CharField(max_length=20, choices=PROCESSING_FACILITY_CHOICES, blank=True, null=True)
    usage_before_disposal = models.CharField(max_length=20, choices=USAGE_CHOICES, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_collections', null=True, blank=True)
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_collections')
    is_approved = models.BooleanField(default=False, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.is_approved and not self.approved_at:
            self.approved_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Waste Collection {self.id}"

class UserMissionDataDays(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    last_reset_at = models.DateTimeField(auto_now_add=True)
    reset_date = models.DateTimeField()
    total_videos_watched = models.IntegerField(default=0)
    current_leaderboard_rank = models.IntegerField(default=0)
    last_donate_date = models.DateTimeField(null=True, blank=True)
    total_donation_count = models.IntegerField(default=0)  # New field


    class Meta:
        verbose_name_plural = "User  Mission Data (Daily)"
    
    @classmethod
    def create_for_user(cls, user):
        try:
            if not user:
                raise ValueError("User cannot be None when creating UserMissionDataDays.")
            instance = cls(user=user)
            instance.reset_date = timezone.now() + timedelta(days=1)
            instance.save()
            print(f"UserMissionDataDays created for user {user.username}")
            return instance
        except Exception as e:
            print(f"Error creating UserMissionDataDays for {user.username}: {e}")
            raise

        
    def save(self, *args, **kwargs):
        try:
            leaderboard_entry = Leaderboard.objects.filter(user=self.user).first()
            if leaderboard_entry:
                self.current_leaderboard_rank = leaderboard_entry.rank

            # Calculate reset_date (1 day after last_reset_at)
            if not self.reset_date or timezone.now() >= self.reset_date:
                self.last_reset_at = timezone.now()
                self.reset_date = self.last_reset_at + timedelta(days=1)
                self.total_videos_watched = 0
                self.current_leaderboard_rank = leaderboard_entry.rank if leaderboard_entry else 0
                self.last_donate_date = None
                self.total_donation_count = 0
            else:
                donations = Donation.objects.filter(
                    user=self.user,
                    status='success',
                    created_at__gte=self.last_reset_at,
                    created_at__lte=self.reset_date
                )
                self.total_donation_count = donations.count()
        except Exception as e:
            print(f"Error in saving UserMissionDataDays for {self.user.username}: {e}")
        super().save(*args, **kwargs)

class UserMissionDataWeeks(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    last_reset_at = models.DateTimeField(auto_now_add=True)
    reset_date = models.DateTimeField()
    total_videos_watched = models.IntegerField(default=0)
    current_leaderboard_rank = models.IntegerField(default=0)
    last_donate_date = models.DateTimeField(null=True, blank=True)
    total_donation_count = models.IntegerField(default=0)  # New field


    class Meta:
        verbose_name_plural = "User  Mission Data (Weekly)"

    @classmethod
    def create_for_user(cls, user):
        if not user:
            raise ValueError("User cannot be None when creating UserMissionDataDays.")
        # Create a new instance for the user
        instance = cls(user=user)
        instance.reset_date = timezone.now() + timedelta(weeks=1)  # Set the reset date
        instance.save()  # Save the instance to the database
        return instance

    def save(self, *args, **kwargs):
        # Get current leaderboard rank
        leaderboard_entry = Leaderboard.objects.filter(user=self.user).first()
        if leaderboard_entry:
            self.current_leaderboard_rank = leaderboard_entry.rank

        # Calculate reset_date (1 week after last_reset_at)
        if not self.reset_date or timezone.now() >= self.reset_date:
            self.last_reset_at = timezone.now()
            self.reset_date = self.last_reset_at + timedelta(weeks=1)
            # Reset mission progress fields
            self.total_videos_watched = 0
            self.current_leaderboard_rank = leaderboard_entry.rank if leaderboard_entry else 0
            self.last_donate_date = None
            self.total_donation_count = 0
        else:
            # Check if user and dates are not None before querying
            if self.user and self.last_reset_at and self.reset_date:
                valid_donation = Donation.objects.filter(
                    user=self.user,
                    status='Success',
                    created_at__gte=self.last_reset_at,
                    created_at__lte=self.reset_date
                ).order_by('-created_at').first()
                
                if valid_donation:
                    self.last_donate_date = valid_donation.created_at
            else:
                self.last_donate_date = None  # Handle None case
            
            self.total_donation_count = Donation.objects.filter(
                user=self.user,
                status='success',
                created_at__gte=self.last_reset_at,
                created_at__lte=self.reset_date
            ).count()

        super().save(*args, **kwargs)

class Notification(models.Model):
    MESSAGE_CHOICES = [
        ('Thank You For The Donation', 'Thank You For The Donation'),
        ('Payment Failed', 'Payment Failed'),
        ('Order Failed', 'Order Failed'),
        ('You Have Successfully Ordered a Product', 'You Have Successfully Ordered a Product'),
        ('You Have Successfully Withdrawn Your Money', 'You Have Successfully Withdrawn Your Money'),
        ('You Have Redeemed A Voucher', 'You Have Redeemed A Voucher'),
    ]

    TYPE_CHOICES = [
        ('Donation', 'Donation'),
        ('Payment Failed', 'Payment Failed'),
        ('Order Failed', 'Order Failed'),
        ('Success Ordered A Product', 'Success Ordered A Product'),
        ('Successful Withdrawing', 'Successful Withdrawing'),
        ('Redeemed A Voucher', 'Redeemed A Voucher'),
    ]

    message = models.CharField(max_length=255, choices=MESSAGE_CHOICES)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.type}: {self.message} for {self.user.username} on {self.created_at}"

    class Meta:
        ordering = ['-created_at']  # Order notifications by creation date, newest first

class Voucher(models.Model):
    CATEGORY_CHOICES = [
        ('Entertainment', 'Entertainment'),
        ('F&B', 'Food & Beverage'),
        ('Shopping', 'Shopping'),
        ('Travel', 'Travel'),
    ]

    title = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField()
    points = models.IntegerField()
    valid_until = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.FileField(upload_to='voucher/', null=True, blank=True)

    def __str__(self):
        return self.title


class VoucherRedeem(models.Model):
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE)
    redeemed_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        is_new = self._state.adding  # Check if this is a new instance
        super().save(*args, **kwargs)

        if is_new:
            # Create a notification for voucher redemption
            Notification.objects.create(
                user=self.user,
                message="You Have Redeemed A Voucher",
                type="Redeemed A Voucher"
            )

            # Subtract points from the user and create a Points entry
            Points.objects.create(
                user=self.user,
                amount=-self.voucher.points,  # Negative points for redemption
                reason=f"Redeemed voucher: {self.voucher.title}",
                is_addition=False,
                is_subtract = True,
            )

    def __str__(self):
        return f"{self.user.username} redeemed {self.voucher.title}"
    
    