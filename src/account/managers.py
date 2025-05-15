from django.contrib.auth.models import BaseUserManager
from auth.logging_config import logger

class CustomUserManager(BaseUserManager):
    def create_user(self, email=None, phone_number=None, password=None, **extra_fields):
        if not email and not phone_number:
            raise ValueError("User must have either an email or phone number")
        
        if email and phone_number:
            raise ValueError("User must have either an email or phone number, not both")
        
        if email:
            email = self.normalize_email(email)
            extra_fields['email'] = email

        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        logger.info(
            'User created through manager',
            extra={
                'user_id': user.id,
                'email': user.email,
                'phone_number': user.phone_number
            }
        )
        return user

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_email_verified', True)
        extra_fields.setdefault('is_phone_verified', True)
        user = self.create_user(email=email, password=password, **extra_fields)
        
        logger.info(
            'Superuser created',
            extra={
                'user_id': user.id,
                'email': user.email,
                'phone_number': user.phone_number
            }
        )
        return user
