from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import *
from djoser.serializers import *
from django.db.models import Sum

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        print("DEBUG: validate() method is being called!")  # Check if validate() runs

        data = super().validate(attrs)  # Get default token response
        request = self.context.get("request")  # Get request object
        
        if request and request.user.is_authenticated:  # Check if user exists
            user = request.user
        else:
            user = self.user if hasattr(self, "user") else None  # Fallback method
        
        print("DEBUG: Retrieved User ->", user)  # Debugging user retrieval

        if user:
            data["user_id"] = user.id  # Include user ID in the response
            print("DEBUG: User ID added to response ->", user.id)

        return data
    

class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'username', 'email', 'password', 'profile_picture', 'name', 'isSeller', 'gender', 'level', 'store_name', 'phone_number', 'store_address', 'id_card_photo', 'virtual_account', 'virtual_account_name', 'bank_issuer', 'total_product')
        extra_kwargs = {
            'gender': {'required': False},  # Gender is not required during registration
            'level': {'required': False},  # Level is not required during registration
            'total_product': {'read_only': True},  # Make total_product read-only
            'created_at': {'read_only': True},
        }

    def create(self, validated_data):
        # Set default values for gender and level
        validated_data['gender'] = validated_data.get('gender', "Prefer Not To Say")
        validated_data['level'] = validated_data.get('level', "Level 1")
        return super().create(validated_data)

class CustomUserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'profile_picture', 'name', 'isSeller', 'gender', 'level', 'store_name', 'phone_number', 'store_address', 'id_card_photo', 'virtual_account', 'virtual_account_name', 'bank_issuer', 'total_product')
        read_only_fields = ('total_product','created_at',)  # Make total_product read-only

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'

class OTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = '__all__'

class SustainabilityImpactSerializer(serializers.ModelSerializer):
    class Meta:
        model = SustainabilityImpact
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    city = serializers.SerializerMethodField()  # Add city as a read-only field
    total_rating = serializers.SerializerMethodField()  # Add total_rating as a read-only field
    formatted_price = serializers.SerializerMethodField()  # Add formatted_price as a read-only field

    class Meta:
        model = Product
        fields = '__all__'  # Include all fields or specify the fields you want

    def get_city(self, obj):
        # Return the city derived from the seller's address
        return obj.city
    
    def get_formatted_price(self, obj):
        # Format the price as Indonesian Rupiah (IDR)
        return f"Rp {obj.price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    def get_total_rating(self, obj):
        # Calculate the average rating from all reviews for this product
        return obj.total_rating

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Construct the full URL for the image using the request object
        request = self.context.get('request')
        if instance.image and request is not None:
            representation['image'] = request.build_absolute_uri(instance.image.url)
        return representation


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'user', 'user_name', 'user_profile_picture', 'product', 
                  'review_text', 'review_star', 'uploaded_at']

    def get_user_name(self, obj):
        return obj.user.name if obj.user.name else obj.user.username

    def get_user_profile_picture(self, obj):
        request = self.context.get('request')  # Get the request context
        if obj.user.profile_picture:
            return request.build_absolute_uri(obj.user.profile_picture.url)  # Construct the full URL
        return None

class ShippingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipping
        fields = '__all__'

class PurchaseSerializer(serializers.ModelSerializer):
    shipping = ShippingSerializer(read_only=True)  # Nested serializer for shipping details
    total_price = serializers.SerializerMethodField()  # Add total_price as a read-only field

    class Meta:
        model = Purchase
        fields = '__all__'
        read_only_fields = ('due_date','created_at',)  # Make total_product read-only

        
    def get_total_price(self, obj):
        # Calculate total_price dynamically
        return obj.total_price

class WasteBankSerializer(serializers.ModelSerializer):
    class Meta:
        model = WasteBank
        fields = '__all__'

class TrashEducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrashEducation
        fields = '__all__'

class MissionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MissionList
        fields = '__all__'

class MissionProgressSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())  # Make user writable
    mission_id = serializers.PrimaryKeyRelatedField(queryset=MissionList.objects.all())  # Make mission writable

    class Meta:
        model = MissionProgress
        fields =  '__all__'  # Include both user and mission

class MissionProgressDetailSerializer(serializers.ModelSerializer):
    mission_id = MissionListSerializer(read_only=True)  # Nest the MissionListSerializer

    class Meta:
        model = MissionProgress
        fields = ['id', 'mission_id', 'mission_progress', 'status', 'updated_at', 'user']

class WasteWrapSerializer(serializers.ModelSerializer):
    class Meta:
        model = WasteWrap
        fields = '__all__'

class DonationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donation
        fields = '__all__'

class LeaderboardSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    profile_picture = serializers.ImageField(source='user.profile_picture', read_only=True)

    class Meta:
        model = Leaderboard
        fields = ['id', 'username', 'profile_picture', 'user_points', 'rank', 'user']
        read_only_fields = ['rank', 'user_points', 'user']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')  # Get the request context
        if instance.user.profile_picture and request is not None:
            representation['profile_picture'] = request.build_absolute_uri(instance.user.profile_picture.url)  # Construct the full URL
        return representation

class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'

class AchievementListSerializer(serializers.ModelSerializer):
    class Meta:
        model = AchievementList
        fields = '__all__'

class UserAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementListSerializer(read_only=True)

    class Meta:
        model = UserAchievement
        fields = ['achievement']
        read_only_fields = ['achievement']  # Make achievement read-only, but allow editing other fields

class ReelVideosSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    profile_picture = serializers.ImageField(source='user.profile_picture', read_only=True)

    class Meta:
        model = ReelVideos
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')  # Get the request context
        if instance.user.profile_picture and request is not None:
            representation['profile_picture'] = request.build_absolute_uri(instance.user.profile_picture.url)  # Construct the full URL
        return representation


class UserSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, read_only=True, source='address_set')
    user_achievements = UserAchievementSerializer(many=True, read_only=True, source='userachievement_set')
    leaderboard = LeaderboardSerializer(read_only=True, source='leaderboard_set.first')
    mission_progresses = MissionProgressSerializer(many=True, read_only=True, source='missionprogress_set')
    total_donations = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'profile_picture', 'name', 'isSeller', 'gender', 'level', 'store_name',
            'phone_number', 'store_address', 'id_card_photo', 'virtual_account', 'virtual_account_name',
            'bank_issuer', 'total_product', 'points', 'total_xp', 'total_donations', 'addresses',
            'user_achievements', 'leaderboard', 'mission_progresses', 'total_balance'
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def get_total_donations(self, obj):
        # Calculate total donations for the user
        return Donation.objects.filter(user=obj).aggregate(total=Sum('amount'))['total'] or 0
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Construct the full URL for the id_card_photo using the request object
        request = self.context.get('request')
        if instance.id_card_photo and request is not None:
            representation['id_card_photo'] = request.build_absolute_uri(instance.id_card_photo.url)
        return representation
    

class WasteImageSerializer(serializers.ModelSerializer):
    waste = serializers.PrimaryKeyRelatedField(queryset=WasteType.objects.all())  # Ganti dari waste_type ke waste

    class Meta:
        model = WasteImage
        fields = ['id', 'waste', 'name', 'image']  # Ganti waste_type ke waste


class MythSerializer(serializers.ModelSerializer):
    class Meta:
        model = Myth
        fields = ['id', 'waste', 'text']

class FactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fact
        fields = ['id', 'waste', 'text']


class ProcessingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessingMethod
        fields = ['id', 'waste', 'title', 'description']

class WasteTypeSerializer(serializers.ModelSerializer):
    images = WasteImageSerializer(many=True, read_only=True)
    myths = MythSerializer(many=True, read_only=True)
    facts = FactSerializer(many=True, read_only=True)
    processing_methods = ProcessingMethodSerializer(many=True, read_only=True)

    class Meta:
        model = WasteType
        fields = ['id', 'name', 'description', 'images', 'myths', 'facts', 'processing_methods']

class RecentDonationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    profile_picture = serializers.ImageField(source='user.profile_picture', read_only=True)

    class Meta:
        model = Donation
        fields = ['id', 'username', 'profile_picture', 'created_at', 'amount', 'message', 'status']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')  # Get the request context
        if instance.user.profile_picture and request is not None:
            representation['profile_picture'] = request.build_absolute_uri(instance.user.profile_picture.url)  # Construct the full URL
        return representation
    
# class WasteCollectionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = WasteCollection
#         fields = '__all__'

class WasteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Waste
        fields = ['id', 'waste_weight', 'waste_type', 'waste_condition']

class WasteCollectionSerializer(serializers.ModelSerializer):
    wastes = WasteSerializer(many=True)  # Nested serializer

    class Meta:
        model = WasteCollection
        fields = ['id', 'wastes', 'processing_facility', 'usage_before_disposal', 'user', 'admin']

    def update(self, instance, validated_data):
        # Update the processing_facility and usage_before_disposal
        instance.processing_facility = validated_data.get('processing_facility', instance.processing_facility)
        instance.usage_before_disposal = validated_data.get('usage_before_disposal', instance.usage_before_disposal)
        instance.save()

        # Handle nested wastes updates
        wastes_data = validated_data.pop('wastes', [])
        instance.wastes.clear()  # Clear existing wastes

        for waste_data in wastes_data:
            waste_id = waste_data.get('id')
            if waste_id:
                # Update existing waste
                waste = Waste.objects.get(id=waste_id)
                for attr, value in waste_data.items():
                    setattr(waste, attr, value)
                waste.save()
                instance.wastes.add(waste)  # Add the updated waste to the collection
            else:
                # Create new waste and add it to the collection
                new_waste = Waste.objects.create(**waste_data)
                instance.wastes.add(new_waste)
        
        admin = validated_data.pop('admin', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if admin:
            instance.admin = admin
        instance.save()

        return instance
    
    def create(self, validated_data):
        # Extract nested wastes data
        wastes_data = validated_data.pop('wastes', [])
        # Create the WasteCollection instance
        waste_collection = WasteCollection.objects.create(**validated_data)

        # Create or associate Waste objects
        for waste_data in wastes_data:
            Waste.objects.create(**waste_data, waste_collections=waste_collection)

        admin = validated_data.pop('admin', None)
        waste_collection = WasteCollection.objects.create(**validated_data)
        if admin:
            waste_collection.admin = admin
            waste_collection.save()

        return waste_collection

class UserMissionDataDaysSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMissionDataDays
        fields = '__all__'
        read_only_fields = ['last_reset_at', 'reset_date', 'total_donation_count']  # Include total_donation_count

class UserMissionDataWeeksSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMissionDataWeeks
        fields = '__all__'
        read_only_fields = ['last_reset_at', 'reset_date', 'total_donation_count']  # Include total_donation_count

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = '__all__'

class VoucherDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = '__all__'  # Include all fields from the Voucher model

class VoucherRedeemSerializer(serializers.ModelSerializer):
    voucher_details = VoucherDetailSerializer(source='voucher', read_only=True)  # Include all voucher details

    class Meta:
        model = VoucherRedeem
        fields = ['id', 'redeemed_at', 'voucher', 'user', 'voucher_details', 'is_used']  # Add voucher_details to the fields

class PointsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Points
        fields =  '__all__' 
        read_only_fields = ['id', 'added_at', 'expires_at']

class PointsExpireListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointsExpire
        fields = '__all__'

class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField(required=True)

class PurchaseDetailSerializer(serializers.ModelSerializer):
    product = ProductSerializer()  # Nested serializer
    address = AddressSerializer()

    class Meta:
        model = Purchase
        fields = '__all__'