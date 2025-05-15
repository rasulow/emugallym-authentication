from django.urls import path
from account.api import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

urlpatterns = [
    # users
    path('users/', views.UserListAPIView.as_view(), name='users-list'),
    
    # token
    path('token/', TokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token-verify'),
    
    # registration
    path('registration/', views.UserRegisterAPIView.as_view(), name='register'),
    
    # verification-phone
    path('registration/verify-phone/', views.UserRegistrationVerifyPhoneAPIView.as_view(), name='verify-phone'),
    path('registration/resend-phone/', views.UserRegistrationResendVerificationPhoneAPIView.as_view(), name='resend-verification-phone'),
    
    # verification-email
    path('registration/verify-email/', views.UserRegistrationVerifyEmailAPIView.as_view(), name='verify-email'),
    path('registration/resend-email/', views.UserRegistrationResendVerificationEmailAPIView.as_view(), name='resend-verification-email'),
]