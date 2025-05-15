from django.contrib import admin
from account import models

@admin.register(models.CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'phone_number', 'is_active', 'is_superuser', 'is_email_verified', 'is_phone_verified')
    
    
@admin.register(models.PhoneVerification)
class CustomPhoneVerificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'phone_number', 'code', 'is_verified', 'created_at')

@admin.register(models.EmailVerification)
class CustomEmailVerificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'email', 'code', 'is_verified', 'created_at')