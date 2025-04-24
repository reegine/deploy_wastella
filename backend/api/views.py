from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from rest_framework.response import Response
from rest_framework import status, generics, viewsets
from .models import *
from .serializers import *
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .utils import generate_otp, send_otp_email
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.db.models import Sum
from rest_framework.decorators import api_view,action
from rest_framework.response import Response
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.decorators import action


User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        print("DEBUG: Received login request with data ->", request.data)

        serializer = self.get_serializer(data=request.data, context={'request': request})  # Pass context
        serializer.is_valid(raise_exception=True)

        tokens = serializer.validated_data  # Tokens now include user_id
        print("DEBUG: Final Response Data ->", tokens)

        return Response(tokens, status=status.HTTP_200_OK)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def partial_update(self, request, *args, **kwargs):
        """
        Override the partial update method to handle balance withdrawal and create notifications.
        """
        user = self.get_object()
        total_balance = user.total_balance
        new_balance = request.data.get("total_balance")

        if new_balance is not None:
            try:
                new_balance = int(new_balance)
            except ValueError:
                return Response({"error": "Invalid balance value provided."}, status=status.HTTP_400_BAD_REQUEST)

            if new_balance < 0 or new_balance > total_balance:
                return Response({"error": "Insufficient balance or invalid amount."}, status=status.HTTP_400_BAD_REQUEST)

            withdrawal_amount = total_balance - new_balance

            # Update the user's balance
            user.total_balance = new_balance
            user.save()

            # Create a notification for the successful withdrawal
            Notification.objects.create(
                user=user,
                message=f"You Have Successfully Withdrawn {withdrawal_amount}",
                type="Successful Withdrawing"
            )

            return Response({"message": "Balance updated successfully.", "withdrawal_amount": withdrawal_amount}, status=status.HTTP_200_OK)

        return super().partial_update(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'], url_path='add-points')
    def add_points(self, request, pk=None):
        """
        Add points to a user.
        """
        user = self.get_object()
        amount = request.data.get('amount')
        reason = request.data.get('reason', "Added via API")

        try:
            amount = int(amount)
            if amount <= 0:
                raise ValueError("Amount must be greater than 0.")

            user.add_points(amount, reason)
            return Response({'message': f'{amount} points added to {user.username}.', 'total_points': user.points}, status=status.HTTP_200_OK)
        except (ValueError, ValidationError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='subtract-points')
    def subtract_points(self, request, pk=None):
        """
        Subtract points from a user.
        """
        user = self.get_object()
        amount = request.data.get('amount')
        reason = request.data.get('reason', "Subtracted via API")

        try:
            amount = int(amount)
            if amount <= 0:
                raise ValueError("Amount must be greater than 0.")

            user.subtract_points(amount, reason)
            return Response({'message': f'{amount} points subtracted from {user.username}.', 'total_points': user.points}, status=status.HTTP_200_OK)
        except (ValueError, ValidationError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

class OTPViewSet(viewsets.ModelViewSet):
    queryset = OTP.objects.all()
    serializer_class = OTPSerializer

class SustainabilityImpactViewSet(viewsets.ModelViewSet):
    queryset = SustainabilityImpact.objects.all()
    serializer_class = SustainabilityImpactSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def create(self, request, *args, **kwargs):
        user_id = request.data.get('user')
        product_id = request.data.get('product')
        review_text = request.data.get('review_text')
        review_star = request.data.get('review_star')

        # Fetch the user and product
        try:
            user = User.objects.get(id=user_id)
            product = Product.objects.get(id=product_id)
        except User.DoesNotExist:
            return Response({'error': 'User  not found'}, status=status.HTTP_404_NOT_FOUND)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        # Create the review instance
        review = Review(
            user=user,
            product=product,
            review_text=review_text,
            review_star=review_star
        )
        review.save()  # Save the review to the database

        # Serialize the review to include user profile picture
        serializer = self.get_serializer(review, context={'request': request})  # Pass request context
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class PurchaseViewSet(viewsets.ModelViewSet):
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer

    def perform_create(self, serializer):
        user = serializer.validated_data['user']
        purchase = serializer.save()
        if purchase.status == 'Success':
            # Create a notification for successful purchase
            self.create_notification(user, 'You Have Successfully Ordered a Product', 'Success Ordered A Product')
        elif purchase.status == 'Canceled':
            # Create a notification for payment failure
            self.create_notification(user, 'Payment Failed', 'Payment Failed')
    
    def perform_update(self, serializer):
        purchase = serializer.save()
        if 'status' in self.request.data:
            new_status = self.request.data['status']
            if new_status in dict(Purchase.STATUS_CHOICES):
                print(f"Updating status in PurchaseViewSet to {new_status}")
                purchase.update_status(new_status)

class WasteBankViewSet(viewsets.ModelViewSet):
    queryset = WasteBank.objects.all()
    serializer_class = WasteBankSerializer

class TrashEducationViewSet(viewsets.ModelViewSet):
    queryset = TrashEducation.objects.all()
    serializer_class = TrashEducationSerializer

class GenerateOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print("Request data:", request.data)  # Debugging: Print the request data
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Generate OTP
        otp = generate_otp()

        # Save OTP to the database
        OTP.objects.filter(user=user).delete()  # Delete any existing OTPs for the user
        otp_instance = OTP.objects.create(user=user, otp=otp)

        # Send OTP to the user's email
        send_otp_email(email, otp)

        return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]  # Allow access without authentication

    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        if not email or not otp:
            return Response({'error': 'Email and OTP are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            otp_instance = OTP.objects.get(user=user, otp=otp)
        except (User.DoesNotExist, OTP.DoesNotExist):
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if OTP is expired
        if otp_instance.is_expired():
            return Response({'error': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)

        # OTP is valid
        return Response({'message': 'OTP verified successfully'}, status=status.HTTP_200_OK)

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]  # Allow access without authentication

    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        new_password = request.data.get('new_password')
        if not email or not otp or not new_password:
            return Response({'error': 'Email, OTP, and new password are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            otp_instance = OTP.objects.get(user=user, otp=otp)
        except (User.DoesNotExist, OTP.DoesNotExist):
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if OTP is expired
        if otp_instance.is_expired():
            return Response({'error': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)

        # Reset the user's password
        user.set_password(new_password)
        user.save()

        # Delete the OTP after successful password reset
        otp_instance.delete()

        return Response({'message': 'Password reset successfully'}, status=status.HTTP_200_OK)
    
class MissionListViewSet(viewsets.ModelViewSet):
    queryset = MissionList.objects.all()
    serializer_class = MissionListSerializer

class MissionProgressViewSet(viewsets.ModelViewSet):
    queryset = MissionProgress.objects.all()
    serializer_class = MissionProgressSerializer

class WasteWrapViewSet(viewsets.ModelViewSet):
    queryset = WasteWrap.objects.all()
    serializer_class = WasteWrapSerializer

class DonationViewSet(viewsets.ModelViewSet):
    queryset = Donation.objects.all()
    serializer_class = DonationSerializer

    def perform_create(self, serializer):
        # Save the donation instance
        donation = serializer.save()
        
        # Create a notification for the user
        self.create_notification(donation.user, 'Thank You For The Donation', 'Donation')

    def create_notification(self, user, message, notification_type):
        """
        Create a notification for a user.
        """
        Notification.objects.create(
            user=user,
            message=message,
            type=notification_type
        )

class LeaderboardViewSet(viewsets.ModelViewSet):
    queryset = Leaderboard.objects.all()
    serializer_class = LeaderboardSerializer

class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer

class AchievementListViewSet(viewsets.ModelViewSet):
    queryset = AchievementList.objects.all()
    serializer_class = AchievementListSerializer

class UserAchievementViewSet(viewsets.ModelViewSet):
    queryset = UserAchievement.objects.all()
    serializer_class = UserAchievementSerializer

class ReelVideosViewSet(viewsets.ModelViewSet):
    queryset = ReelVideos.objects.all()
    serializer_class = ReelVideosSerializer

@api_view(['GET'])
def total_donations(request):
    total = Donation.objects.aggregate(total=Sum('amount'))['total'] or 0
    return Response({'total_donations': total})


class ProductReviewsView(APIView):
    def get(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
            reviews = Review.objects.filter(product=product).order_by('-uploaded_at')
            serializer = ReviewSerializer(reviews, many=True, context={'request': request})  # Pass request context
            return Response(serializer.data)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class ProductByCategoryView(APIView):
    def get(self, request, category):
        # Filter products by the given category
        products = Product.objects.filter(category=category)
        serializer = ProductSerializer(products, many=True, context={'request': request})  # Pass request context
        return Response(serializer.data)
    
class UserAddressListView(generics.ListAPIView):
    serializer_class = AddressSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return Address.objects.filter(user_id=user_id)
    
class SellerPurchasesView(APIView):
    def get(self, request, seller_id):
        # Fetch the seller's information
        try:
            seller = User.objects.get(id=seller_id)
        except User.DoesNotExist:
            return Response({'error': 'Seller not found'}, status=status.HTTP_404_NOT_FOUND)

        # Filter purchases where the product's seller matches the given seller_id
        purchases = Purchase.objects.filter(product__seller_id=seller_id).select_related('product')
        
        # Serialize the purchases with product details
        purchase_data = []
        for purchase in purchases:
            purchase_serializer = PurchaseSerializer(purchase)
            product_serializer = ProductSerializer(purchase.product, context={'request': request})  # Pass request context
            purchase_info = purchase_serializer.data
            purchase_info['product'] = product_serializer.data  # Add product details to purchase info
            purchase_data.append(purchase_info)

        # Serialize the seller's data with request context
        seller_serializer = UserSerializer(seller, context={'request': request})

        # Combine both purchase data and seller data into a single response
        response_data = {
            'seller': seller_serializer.data,
            'purchases': purchase_data
        }

        return Response(response_data)
    
class SellerProductsView(APIView):
    def get(self, request, seller_id):
        # Fetch the seller's information
        try:
            seller = User.objects.get(id=seller_id)
        except User.DoesNotExist:
            return Response({'error': 'Seller not found'}, status=status.HTTP_404_NOT_FOUND)

        # Fetch products for the given seller_id
        products = Product.objects.filter(seller_id=seller_id)

        # Serialize the products
        product_serializer = ProductSerializer(products, many=True, context={'request': request})

        # Serialize the seller's information
        seller_serializer = CustomUserSerializer(seller, context={'request': request})

        # Combine both seller information and products into a single response
        response_data = {
            'seller': seller_serializer.data,
            'products': product_serializer.data
        }

        return Response(response_data)
    
class UserPurchasesView(APIView):
    def get(self, request, user_id):
        # Fetch the user's information
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User  not found'}, status=status.HTTP_404_NOT_FOUND)

        # Filter purchases where the user matches the given user_id
        purchases = Purchase.objects.filter(user_id=user_id).select_related('product', 'shipping')

        # Serialize the purchases with product details
        purchase_data = []
        for purchase in purchases:
            purchase_serializer = PurchaseSerializer(purchase)
            product_serializer = ProductSerializer(purchase.product, context={'request': request})  # Pass request context
            
            # Add seller's store_name to the product data
            product_data = product_serializer.data
            product_data['store_name'] = purchase.product.seller.store_name  # Add store_name

            purchase_info = purchase_serializer.data
            purchase_info['product'] = product_data  # Add product details to purchase info
            purchase_data.append(purchase_info)

        return Response(purchase_data)
    
class ProductSearchView(APIView):
    def get(self, request):
        print("DEBUG: Search endpoint hit!")  # Check if this prints in console
        query = request.GET.get('q', '').strip()
        print(f"DEBUG: Search query: {query}")  # Verify the query is received
        
        if not query:
            return Response({"error": "Search query parameter 'q' is required"}, 
                          status=status.HTTP_400_BAD_REQUEST)

        products = Product.objects.filter(title__icontains=query)
        print(f"DEBUG: Found {products.count()} products")  # Check how many products match
        
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

class BestRatedProductsView(APIView):
    def get(self, request):
        try:
            # Fetch the top 5 products ordered by total_rating in descending order
            top_rated_products = Product.objects.order_by('-total_rating')[:5]

            # Serialize the products
            serializer = ProductSerializer(top_rated_products, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdatePurchaseStatusView(APIView):
    def patch(self, request, purchase_id):
        try:
            purchase = Purchase.objects.get(id=purchase_id)
        except Purchase.DoesNotExist:
            return Response({'error': 'Purchase not found'}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        if new_status not in dict(Purchase.STATUS_CHOICES):
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

        # Update the purchase status
        purchase.update_status(new_status)

        return Response({'message': 'Purchase status updated successfully'}, status=status.HTTP_200_OK)
    
class WasteTypeViewSet(viewsets.ModelViewSet):
    queryset = WasteType.objects.all()
    serializer_class = WasteTypeSerializer

class WasteImageViewSet(viewsets.ModelViewSet):
    queryset = WasteImage.objects.all()
    serializer_class = WasteImageSerializer

class MythViewSet(viewsets.ModelViewSet):
    queryset = Myth.objects.all()
    serializer_class = MythSerializer

class FactViewSet(viewsets.ModelViewSet):
    queryset = Fact.objects.all()
    serializer_class = FactSerializer

class ProcessingMethodViewSet(viewsets.ModelViewSet):
    queryset = ProcessingMethod.objects.all()
    serializer_class = ProcessingMethodSerializer

class RecentDonationsView(APIView):
    def get(self, request):
        # Fetch the top 3 most recent donations
        recent_donations = Donation.objects.order_by('-created_at')[:3]
        serializer = RecentDonationSerializer(recent_donations, many=True, context={'request': request})  # Pass request context
        return Response(serializer.data, status=status.HTTP_200_OK)


# class WasteCollectionViewSet(viewsets.ModelViewSet):
#     queryset = WasteCollection.objects.all()
#     serializer_class = WasteCollectionSerializer

class WasteCollectionViewSet(viewsets.ModelViewSet):
    queryset = WasteCollection.objects.all()
    serializer_class = WasteCollectionSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

class WasteViewSet(viewsets.ModelViewSet):
    queryset = Waste.objects.all()
    serializer_class = WasteSerializer

class UserMissionProgressView(APIView):
    def get(self, request, user_id):
        # Fetch the mission progress for the specified user
        mission_progress = MissionProgress.objects.filter(user_id=user_id)

        # Serialize the mission progress data with mission details
        serializer = MissionProgressDetailSerializer(mission_progress, many=True, context={'request': request})

        return Response(serializer.data)

class UserMissionDataDaysViewSet(viewsets.ModelViewSet):
    queryset = UserMissionDataDays.objects.all()
    serializer_class = UserMissionDataDaysSerializer
    permission_classes = [AllowAny]  # Changed from IsAuthenticated to AllowAny

    def get_queryset(self):
        # If user is authenticated, filter by user
        if self.request.user.is_authenticated:
            return self.queryset.filter(user=self.request.user)
        # If not authenticated, return all
        return self.queryset.all()  # Allow public access to all data

class UserMissionDataWeeksViewSet(viewsets.ModelViewSet):
    queryset = UserMissionDataWeeks.objects.all()
    serializer_class = UserMissionDataWeeksSerializer
    permission_classes = [AllowAny]  # Changed from IsAuthenticated to AllowAny

    def get_queryset(self):
        # If user is authenticated, filter by user
        if self.request.user.is_authenticated:
            return self.queryset.filter(user=self.request.user)
        # If not authenticated, return all
        return self.queryset.all()  # Allow public access to all data
    
class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def create_notification(self, user, message, notification_type):
        notification = Notification.objects.create(
            user=user,
            message=message,
            type=notification_type
        )
        return notification
    
    @action(detail=True, methods=['post'], url_path='mark-as-read')
    def mark_as_read(self, request, pk=None):
        """Mark a notification as read."""
        try:
            notification = self.get_object()
            notification.is_read = True
            notification.save()
            return Response({'status': 'Notification marked as read'}, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_queryset(self):
        """
        Override the default queryset to filter by user ID.
        """
        user_id = self.request.query_params.get('user_id')
        if user_id:
            return self.queryset.filter(user_id=user_id)
        return self.queryset
    
    @action(detail=False, methods=['get'], url_path='all-is-read')
    def all_is_read(self, request):
        """
        Check if all notifications for a user are read.
        """
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Filter notifications for the user
            user_notifications = Notification.objects.filter(user_id=user_id)
            
            # Check if any notification is unread
            all_read = not user_notifications.filter(is_read=False).exists()

            return Response({'all_is_read': all_read}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class UserMissionDataDaysByUserIdView(APIView):
    """
    Endpoint to fetch UserMissionDataDays by user ID.
    """
    permission_classes = [AllowAny]  # Adjust permission as needed

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        mission_data_days = UserMissionDataDays.objects.filter(user=user)
        serializer = UserMissionDataDaysSerializer(mission_data_days, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserMissionDataWeeksByUserIdView(APIView):
    """
    Endpoint to fetch UserMissionDataWeeks by user ID.
    """
    permission_classes = [AllowAny]  # Adjust permission as needed

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        mission_data_weeks = UserMissionDataWeeks.objects.filter(user=user)
        serializer = UserMissionDataWeeksSerializer(mission_data_weeks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class VoucherViewSet(viewsets.ModelViewSet):
    queryset = Voucher.objects.all().order_by('-created_at')
    serializer_class = VoucherSerializer

class VoucherRedeemViewSet(viewsets.ModelViewSet):
    queryset = VoucherRedeem.objects.all()
    serializer_class = VoucherRedeemSerializer

    def perform_create(self, serializer):
        # Save the VoucherRedeem instance
        voucher_redeem = serializer.save()

        # Get the user associated with the voucher redeem
        user = voucher_redeem.user

        # Send a thank-you email to the user
        self.send_thank_you_email(user.email, voucher_redeem.voucher)

    def send_thank_you_email(self, user_email, voucher):
        subject = "Thank You for Redeeming Your Voucher!"
        message = f"Dear User,\n\nThank you for redeeming your voucher: {voucher.title}.\n\nEnjoy your benefits!\n\nBest Regards,\nWastella"
        from_email = settings.EMAIL_HOST_USER  # Use the email configured in settings

        send_mail(subject, message, from_email, [user_email])

class UserVoucherRedeemView(APIView):
    def get(self, request, user_id):
        # Fetch the voucher redemptions for the specified user
        voucher_redeems = VoucherRedeem.objects.filter(user_id=user_id).order_by('-redeemed_at')

        # Serialize the data
        serializer = VoucherRedeemSerializer(voucher_redeems, many=True, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)
    
class PointsViewSet(viewsets.ModelViewSet):
    queryset = Points.objects.all()
    serializer_class = PointsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Restrict points to only those belonging to the authenticated user.
        """
        return self.queryset.filter(user=self.request.user)

    # @action(detail=False, methods=['get'], url_path='remove-expired')
    # def remove_expired(self, request):
    #     """
    #     Endpoint to remove expired points.
    #     """
    #     Points.remove_expired_points()
    #     return Response({'message': 'Expired points removed successfully.'}, status=status.HTTP_200_OK)

class UserPointsHistoryView(generics.ListAPIView):
    """
    API view to retrieve the points history of a specific user.
    """
    serializer_class = PointsSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return Points.objects.filter(user_id=user_id).order_by('-added_at')  # Order by most recent first
    
class ExpirePointsListViewSet(viewsets.ModelViewSet):
    queryset = PointsExpire.objects.all()
    serializer_class = PointsExpireListSerializer

class UserExpirePointsView(generics.ListAPIView):
    """
    API view to retrieve expired points for a specific user.
    """
    serializer_class = PointsExpireListSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return PointsExpire.objects.filter(user_id=user_id).order_by('-expired_at')  # Order by most recent first
    
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.utils.crypto import get_random_string
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import datetime
from django.core.files.base import ContentFile,File
import requests as http_requests
from urllib.parse import urlparse
import os
from django.db import IntegrityError
from django.core.exceptions import ValidationError

# class GoogleLoginView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request, *args, **kwargs):
#         serializer = GoogleLoginSerializer(data=request.data)
#         if serializer.is_valid():
#             id_token_string = serializer.validated_data.get('id_token')

#             # ✅ Fix applied here
#             if isinstance(id_token_string, list):
#                 id_token_string = id_token_string[0] if id_token_string else ''
#             elif not isinstance(id_token_string, str):
#                 id_token_string = str(id_token_string)

#             if not id_token_string:
#                 return Response({'error': 'No ID token provided.'}, status=status.HTTP_400_BAD_REQUEST)

#             try:
#                 print(f"Received ID token: {id_token_string}")
#                 client_id = "333712084041-f4m3sram6rmi05a1pamqefrjbo8rse7m.apps.googleusercontent.com"

#                 idinfo = id_token.verify_oauth2_token(
#                     id_token_string,
#                     requests.Request(),
#                     client_id
#                 )
#                 print(f"Decoded ID token info: {idinfo}")

#                 exp = idinfo.get('exp')
#                 current_time = int(datetime.now().timestamp())
#                 print(f"Token expiration time: {exp}, Current server time: {current_time}")

#                 if exp < current_time:
#                     raise ValueError(f"Token expired, {exp} < {current_time}")

#                 email = idinfo.get('email')
#                 if not email or email.strip() == "":
#                     raise ValueError("Email is required but was not provided.")
#                 print(f"Validated email: {email}")

#                 username = idinfo.get('email', '').split('@')[0]
#                 if not username or username.strip() == "":
#                     raise ValueError("Username could not be generated from email.")
#                 print(f"Validated username: {username}")

#                 given_name = idinfo.get('given_name', '') or ''
#                 family_name = idinfo.get('family_name', '') or ''
#                 full_name = f"{given_name} {family_name}".strip() or username

#                 profile_picture_url = idinfo.get('picture')
#                 profile_picture = None
#                 if profile_picture_url:
#                     try:
#                         response = http_requests.get(profile_picture_url)
#                         if response.status_code == 200:
#                             file_name = os.path.basename(urlparse(profile_picture_url).path)
#                             if not file_name or '.' not in file_name:
#                                 file_name = f"profile_{username}.jpg"
#                             profile_picture = ContentFile(response.content, name=file_name)
#                             print(f"Successfully downloaded profile picture for {username}")
#                     except Exception as e:
#                         print(f"Error downloading profile picture: {e}")
#                         profile_picture = None

#                 if not profile_picture:
#                     default_picture_path = os.path.join(settings.MEDIA_ROOT, 'default_profile.jpg')
#                     try:
#                         with open(default_picture_path, 'rb') as f:
#                             profile_picture = File(f, name='default_profile.jpg')
#                             print("Using default profile picture from media directory.")
#                     except Exception as e:
#                         print(f"Error loading default profile picture from media: {e}")
#                         profile_picture = None

#                 if not profile_picture:
#                     print("No profile picture available; proceeding without it.")

#                 with transaction.atomic():
#                     random_password = get_random_string(length=32)
#                     hashed_password = make_password(random_password)

#                     user_defaults = {
#                         'username': username,
#                         'name': full_name,
#                         'is_active': True,
#                         'password': hashed_password,
#                         'profile_picture': profile_picture if profile_picture else None,
#                     }

#                     # Filter out None values explicitly
#                     user_defaults = {k: v for k, v in user_defaults.items() if v is not None}
#                     print(f"Filtered user defaults (no None values): {user_defaults}")

#                     print('ini email yg sblm get or create:', email)

#                     try:
#                         user, created = User.objects.get_or_create(
#                             email=email,
#                             defaults=user_defaults
#                         )
#                     except Exception as e:
#                         print("Error during get_or_create:")
#                         print(f"Email: {email}")
#                         print(f"User defaults: {user_defaults}")
#                         import traceback
#                         traceback.print_exc()
#                         raise

#                 if created:
#                     print(f"New user created: {user.username}")
#                 else:
#                     print(f"Existing user retrieved: {user.username}")

#                 refresh = RefreshToken.for_user(user)
#                 access = str(refresh.access_token)

#                 return Response({
#                     'refresh': str(refresh),
#                     'access': access,
#                     'user': {
#                         'id': user.id,
#                         'username': user.username,
#                         'email': user.email,
#                         'name': user.name,
#                         'profile_picture': user.profile_picture.url if user.profile_picture else '',
#                     }
#                 }, status=status.HTTP_200_OK)

#             except ValueError as e:
#                 if "Token expired" in str(e):
#                     return Response({'error': 'Token expired', 'details': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
#                 print(f"Token verification failed: {e}")
#                 return Response({'error': 'Invalid token', 'details': str(e)}, status=status.HTTP_400_BAD_REQUEST)
#             except (IntegrityError, ValidationError) as e:
#                 print(f"Database error: {e}")
#                 return Response({'error': 'Database error', 'details': str(e)}, status=status.HTTP_400_BAD_REQUEST)
#             except Exception as e:
#                 print(f"Unexpected error: {e}")
#                 import traceback
#                 traceback.print_exc()
#                 return Response({'error': 'Server error', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = GoogleLoginSerializer(data=request.data)
        if serializer.is_valid():
            id_token_string = serializer.validated_data.get('id_token')

            if isinstance(id_token_string, list):
                id_token_string = id_token_string[0] if id_token_string else ''
            elif not isinstance(id_token_string, str):
                id_token_string = str(id_token_string)

            if not id_token_string:
                return Response({'error': 'No ID token provided.'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                print(f"Received ID token: {id_token_string}")
                client_id = "333712084041-f4m3sram6rmi05a1pamqefrjbo8rse7m.apps.googleusercontent.com"

                idinfo = id_token.verify_oauth2_token(
                    id_token_string,
                    requests.Request(),
                    client_id
                )
                print(f"Decoded ID token info: {idinfo}")

                exp = idinfo.get('exp')
                current_time = int(datetime.now().timestamp())
                print(f"Token expiration time: {exp}, Current server time: {current_time}")

                if exp < current_time:
                    raise ValueError(f"Token expired, {exp} < {current_time}")

                email = idinfo.get('email')
                if not email or email.strip() == "":
                    raise ValueError("Email is required but was not provided.")
                print(f"Validated email: {email}")

                username = idinfo.get('email', '').split('@')[0]
                if not username or username.strip() == "":
                    raise ValueError("Username could not be generated from email.")
                print(f"Validated username: {username}")

                given_name = idinfo.get('given_name', '') or ''
                family_name = idinfo.get('family_name', '') or ''
                full_name = f"{given_name} {family_name}".strip() or username

                profile_picture_url = idinfo.get('picture')
                profile_picture = None
                if profile_picture_url:
                    try:
                        response = http_requests.get(profile_picture_url)
                        if response.status_code == 200:
                            file_name = os.path.basename(urlparse(profile_picture_url).path)
                            if not file_name or '.' not in file_name:
                                file_name = f"profile_{username}.jpg"
                            profile_picture = ContentFile(response.content, name=file_name)
                            print(f"Successfully downloaded profile picture for {username}")
                    except Exception as e:
                        print(f"Error downloading profile picture: {e}")
                        profile_picture = None

                if not profile_picture:
                    default_picture_path = os.path.join(settings.MEDIA_ROOT, 'default_profile.jpg')
                    try:
                        with open(default_picture_path, 'rb') as f:
                            profile_picture = File(f, name='default_profile.jpg')
                            print("Using default profile picture from media directory.")
                    except Exception as e:
                        print(f"Error loading default profile picture from media: {e}")
                        profile_picture = None

                if not profile_picture:
                    print("No profile picture available; proceeding without it.")

                with transaction.atomic():
                    random_password = get_random_string(length=32)
                    hashed_password = make_password(random_password)

                    user_defaults = {
                        'username': username,
                        'name': full_name,
                        'is_active': True,
                        'password': hashed_password,
                        'profile_picture': profile_picture if profile_picture else None,
                    }

                    # Filter out None values explicitly
                    user_defaults = {k: v for k, v in user_defaults.items() if v is not None}
                    print(f"Filtered user defaults (no None values): {user_defaults}")

                    print('Email before get_or_create:', email)

                    existing_user = User.objects.filter(email=email).first()
                    print("Existing user ID:", existing_user.id if existing_user else "No user yet")

                    try:
                        user, created = User.objects.get_or_create(
                            email=email,
                            defaults=user_defaults
                        )
                    except Exception as e:
                        print("Error during get_or_create:")
                        print(f"Email: {email}")
                        print(f"User  defaults: {user_defaults}")
                        import traceback
                        traceback.print_exc()
                        raise

                if created:
                    print(f"New user created: {user.username}")
                else:
                    print(f"Existing user retrieved: {user.username}")

                refresh = RefreshToken.for_user(user)
                access = str(refresh.access_token)

                return Response({
                    'refresh': str(refresh),
                    'access': access,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'name': user.name,
                        'profile_picture': user.profile_picture.url if user.profile_picture else '',
                    }
                }, status=status.HTTP_200_OK)

            except ValueError as e:
                if "Token expired" in str(e):
                    return Response({'error': 'Token expired', 'details': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
                print(f"Token verification failed: {e}")
                return Response({'error': 'Invalid token', 'details': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except (IntegrityError, ValidationError) as e:
                print(f"Database error: {e}")
                return Response({'error': 'Database error', 'details': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(f"Unexpected error: {e}")
                import traceback
                traceback.print_exc()
                return Response({'error': 'Server error', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)