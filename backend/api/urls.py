from django.urls import path, include
from .views import *
from rest_framework.routers import DefaultRouter
from .views import CustomTokenObtainPairView 
from rest_framework_simplejwt.views import TokenBlacklistView
from .views import GenerateOTPView, VerifyOTPView, ResetPasswordView
from django.conf import settings
from django.conf.urls.static import static


router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'addresses', AddressViewSet)
router.register(r'otps', OTPViewSet)
router.register(r'sustainability-impacts', SustainabilityImpactViewSet)
router.register(r'products', ProductViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'purchases', PurchaseViewSet)
router.register(r'wastebank', WasteBankViewSet)  # Endpoint: /wastebank/
router.register(r'trash-educations', TrashEducationViewSet)
router.register(r'mission-lists', MissionListViewSet)
router.register(r'mission-progresses', MissionProgressViewSet)
router.register(r'waste-wraps', WasteWrapViewSet)
router.register(r'donations', DonationViewSet)
router.register(r'leaderboards', LeaderboardViewSet)
router.register(r'faqs', FAQViewSet)
router.register(r'achievement-lists', AchievementListViewSet)
router.register(r'user-achievements', UserAchievementViewSet)
router.register(r'reel-videos', ReelVideosViewSet)
router.register(r'waste-types', WasteTypeViewSet)
router.register(r'waste-images', WasteImageViewSet)
router.register(r'myths', MythViewSet)
router.register(r'facts', FactViewSet)
router.register(r'processing-methods', ProcessingMethodViewSet)
router.register(r'waste-collections', WasteCollectionViewSet, basename='wastecollection')
router.register(r'wastes', WasteViewSet, basename='wastes')
router.register(r'user-mission-data-days', UserMissionDataDaysViewSet, basename='user-mission-data-days')
router.register(r'user-mission-data-weeks', UserMissionDataWeeksViewSet, basename='user-mission-data-weeks')
router.register(r'notifications', NotificationViewSet, basename='notifications')
router.register(r'vouchers', VoucherViewSet, basename='voucher')  # Register VoucherViewSet
router.register(r'voucher-redeems', VoucherRedeemViewSet, basename='voucher-redeem')  # Register VoucherRedeemViewSet
router.register(r'points', PointsViewSet, basename='points')  # Register VoucherViewSet
router.register(r'points-expire', ExpirePointsListViewSet, basename='points-expire')  # Register VoucherViewSet



urlpatterns = [
    
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),  # Include Djoser's URLs
    path('auth/jwt/create/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/jwt/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('generate-otp/', GenerateOTPView.as_view(), name='generate_otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('total-donations/', total_donations, name='total_donations'),
    path('products/<int:product_id>/reviews/', ProductReviewsView.as_view(), name='product-reviews'),
    path('products/category/<str:category>/', ProductByCategoryView.as_view(), name='products_by_category'),
    path('users/<int:user_id>/addresses/', UserAddressListView.as_view(), name='user_addresses'),
    path('sellers/<int:seller_id>/purchases/', SellerPurchasesView.as_view(), name='seller_purchases'),
    path('sellers/<int:seller_id>/products/', SellerProductsView.as_view(), name='seller_products'),
    path('users/<int:user_id>/purchases/', UserPurchasesView.as_view(), name='user_purchases'),
    path('product/search/', ProductSearchView.as_view(), name='product-search'),
    path('product/best-rated/', BestRatedProductsView.as_view(), name='best-rated-products'),
    path('purchases/<int:purchase_id>/update-status/', UpdatePurchaseStatusView.as_view(), name='update_purchase_status'),
    path('recent-donations/', RecentDonationsView.as_view(), name='recent_donations'),
    path('users/<int:user_id>/mission-progress/', UserMissionProgressView.as_view(), name='user_mission_progress'),
    path('notifications/<int:pk>/mark-as-read/', NotificationViewSet.as_view({'post': 'mark_as_read'}), name='mark_as_read'),
    path('users/<int:user_id>/mission-data-days/', UserMissionDataDaysByUserIdView.as_view(), name='mission_data_days_by_user'),
    path('users/<int:user_id>/mission-data-weeks/', UserMissionDataWeeksByUserIdView.as_view(), name='mission_data_weeks_by_user'),
    path('users/<int:user_id>/voucher-redeems/', UserVoucherRedeemView.as_view(), name='user-voucher-redeems'),
    path('notifications/all-is-read/', NotificationViewSet.as_view({'get': 'all_is_read'}), name='all_is_read'),
    path('users/<int:user_id>/points-history/', UserPointsHistoryView.as_view(), name='user_points_history'),
    path('users/<int:user_id>/expired-points/', UserExpirePointsView.as_view(), name='user-expired-points'),
    path('auth/google/', GoogleLoginView.as_view(), name='google_login'),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)