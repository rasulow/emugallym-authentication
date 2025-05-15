from django.contrib.auth.backends import BaseBackend
from account.models import CustomUser

class EmailOrPhoneAuthenticationBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        username = username or kwargs.get('phone_number') or kwargs.get('email')
        try:
            user = CustomUser.objects.get(email=username)
        except CustomUser.DoesNotExist:
            try:
                user = CustomUser.objects.get(phone_number=username)
            except CustomUser.DoesNotExist:
                return None

        if not user.check_password(password):
            return None

        if user.is_active and (user.is_email_verified or user.is_phone_verified):
            return user
        else:
            return None

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None
