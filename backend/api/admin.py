from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# Custom UserAdmin for your custom User model
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'email', 'username', 'name', 'isSeller', 'is_staff', 'is_superuser')
    list_filter = ('isSeller', 'is_staff', 'is_superuser')
    search_fields = ('email', 'username', 'name')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('username', 'name', 'profile_picture', 'gender', 'level','total_balance','points', 'total_xp', 'total_donations')}),
        ('Seller Info', {'fields': ('isSeller', 'store_name', 'phone_number', 'store_address', 'id_card_photo', 'virtual_account', 'virtual_account_name', 'bank_issuer', 'total_product')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login',)}),  # Removed 'created_at' and 'updated_at' from here
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')  # Add 'created_at' and 'updated_at' to readonly_fields
    ordering = ('email',)

# Register the User model with the custom UserAdmin
admin.site.register(User, CustomUserAdmin)

# Register other models
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'phone_number', 'city', 'province')
    search_fields = ('user__email', 'name', 'city', 'province')
    list_filter = ('city', 'province')

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'otp', 'created_at', 'expires_at')
    search_fields = ('user__email', 'otp')
    list_filter = ('created_at', 'expires_at')

@admin.register(SustainabilityImpact)
class SustainabilityImpactAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_tree', 'total_recycled', 'total_carbon', 'total_co2')
    search_fields = ('user__email',)
    list_filter = ('total_tree', 'total_recycled')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'seller', 'title', 'price', 'stock', 'category', 'uploaded_at')
    search_fields = ('seller__email', 'title', 'category')
    list_filter = ('category', 'uploaded_at')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'user', 'review_star', 'uploaded_at')
    search_fields = ('product__title', 'user__email')
    list_filter = ('review_star', 'uploaded_at')

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'user', 'status', 'created_at')
    search_fields = ('product__title', 'user__email')
    list_filter = ('status', 'created_at')

@admin.register(WasteBank)
class WasteBankAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'latitude', 'longitude', 'address', 'created_at')  # Use 'id' instead of 'bank_id'
    search_fields = ('name', 'address')
    list_filter = ('created_at',)  # Remove 'city' from list_filter

@admin.register(TrashEducation)
class TrashEducationAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'type', 'created_at')  # Use 'id' instead of 'education_id'
    search_fields = ('title', 'type')
    list_filter = ('type', 'created_at')


# @admin.register(WasteCollection)
# class WasteCollectionAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'waste_type', 'waste_weight', 'is_approved', 'admin')
#     list_filter = ('is_approved', 'waste_type')
#     search_fields = ('user__username', 'admin__username')

admin.site.register(Waste)
admin.site.register(WasteCollection)

admin.site.register(UserMissionDataDays)
admin.site.register(UserMissionDataWeeks)