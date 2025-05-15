from django.db import models
from django.contrib.auth.models import PermissionsMixin, AbstractBaseUser
from account.managers import CustomUserManager
from auth.logging_config import logger
import random

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new:
            logger.info(
                'New user created',
                extra={
                    'user_id': self.id,
                    'email': self.email,
                    'phone_number': self.phone_number
                }
            )
        else:
            logger.info(
                'User updated',
                extra={
                    'user_id': self.id,
                    'email': self.email,
                    'phone_number': self.phone_number
                }
            )

    objects = CustomUserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []
    
    def get_fullname(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.get_fullname()
    
    class Meta:
        db_table = 'user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-id']
    
    
class PhoneVerification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="phone_verifications")
    phone_number = models.CharField(max_length=20, unique=True)
    code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'phone_verification'
        verbose_name = 'Phone Verification'
        verbose_name_plural = 'Phone Verifications'
        ordering = ['-id']

    def __str__(self):
        return f"{self.phone_number} - {'Verified' if self.is_verified else 'Not Verified'}"


    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new:
            logger.info(
                'New phone verification created',
                extra={
                    'user_id': self.user.id,
                    'phone_number': self.phone_number
                }
            )

        if self.is_verified and not self.user.is_phone_verified:
            self.user.is_phone_verified = True
            self.user.save()
            logger.info(
                'Phone number verified successfully',
                extra={
                    'user_id': self.user.id,
                    'phone_number': self.phone_number
                }
            )

    @staticmethod
    def gen_code():
        return str(random.randint(100000, 999999))


class EmailVerification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="email_verifications")
    email = models.EmailField(unique=True)
    code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'email_verification'
        verbose_name = 'Email Verification'
        verbose_name_plural = 'Email Verifications'
        ordering = ['-id']

    def __str__(self):
        return f"{self.email} - {'Verified' if self.is_verified else 'Not Verified'}"


    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new:
            logger.info(
                'New email verification created',
                extra={
                    'user_id': self.user.id,
                    'email': self.email
                }
            )

        if self.is_verified and not self.user.is_email_verified:
            self.user.is_email_verified = True
            self.user.save()
            logger.info(
                'Email verified successfully',
                extra={
                    'user_id': self.user.id,
                    'email': self.email
                }
            )

    @staticmethod
    def gen_code():
        return str(random.randint(100000, 999999))