from os import environ as env
from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers
from dotenv import load_dotenv
from account import models, tasks, services, exceptions
from auth.logging_config import logger
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

load_dotenv()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['role'] = user.role 
        token['user_id'] = user.id

        return token
    
    
class UsersListSerializer(serializers.ModelSerializer):
    """Serializer for listing all users."""
    class Meta:
        model = models.CustomUser
        fields = ('id', 'email', 'phone_number', 'first_name', 'last_name', 'role', 'educational_institution', 'is_active', 'is_phone_verified')


class UserRegisterSerializer(serializers.Serializer):
    """Serializer for user registration."""
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    password1 = serializers.CharField(
        label="Password",
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True,
    )
    password2 = serializers.CharField(
        label="Password confirmation",
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True,
    )
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    role = serializers.ChoiceField(choices=models.CustomUser.ROLE_CHOICES, default='teacher')
    educational_institution = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        """Validate registration data before creating a user."""
        email = attrs.get('email')
        phone_number = attrs.get('phone_number')
        password1 = attrs.get('password1')
        password2 = attrs.get('password2')

        if not email and not phone_number:
            logger.warning('Registration attempt without email and phone number')
            raise serializers.ValidationError(
                {'non_field_errors': 'Either email or phone number is required.'}
            )

        if password1 != password2:
            logger.warning('Registration attempt with mismatched passwords')
            raise serializers.ValidationError({'password2': 'Passwords must match.'})

        if email and models.CustomUser.objects.filter(email=email).exists():
            logger.warning(f'Registration attempt with existing email: {email}')
            raise serializers.ValidationError({'email': 'A user with this email already exists.'})

        if phone_number and models.CustomUser.objects.filter(phone_number=phone_number).exists():
            logger.warning(f'Registration attempt with existing phone number: {phone_number}')
            raise serializers.ValidationError(
                {'phone_number': 'A user with this phone number already exists.'}
            )

        return attrs

    def create(self, validated_data):
        try:
            verification_code = models.EmailVerification.gen_code()
            user = self._create_user(validated_data)
            self._handle_verification(user, validated_data, verification_code)
            return user
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}", exc_info=True)
            raise serializers.ValidationError({'non_field_errors': f'Error creating user: {str(e)}'})
        
    def _create_user(self, data):
        common_fields = {
            "password": data["password1"],
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "role": data["role"],
            "educational_institution": data["educational_institution"],
        }

        if data.get("phone_number"):
            user = models.CustomUser.objects.create_user(
                phone_number=data["phone_number"],
                **common_fields
            )
            logger.info(f'New user created. ID: {user.id}, Phone: {user.phone_number}')
        elif data.get("email"):
            user = models.CustomUser.objects.create_user(
                email=data["email"],
                **common_fields
            )
            logger.info(f'New user created. ID: {user.id}, Email: {user.email}')
        else:
            raise serializers.ValidationError({'non_field_errors': 'Either phone number or email must be provided.'})

        return user

    def _handle_verification(self, user, data, code):
        if data.get("phone_number"):
            self._send_sms_verification(data["phone_number"], code)

            phone_verification = models.PhoneVerification.objects.create(
                user=user,
                phone_number=data["phone_number"],
                code=code,
                is_verified=False
            )
            logger.info(f'Phone verification created for user {user.id}')
            return

        if data.get("email"):
            self._send_email_verification(data["email"], code)

            email_verification = models.EmailVerification.objects.create(
                user=user,
                email=data["email"],
                code=code,
                is_verified=False
            )
            logger.info(f'Email verification created for user {user.id}')
            return
        
    def _send_sms_verification(self, phone_number, code):
        if services.send_sms(phone_number, code):
            logger.info(f'SMS sent to {phone_number} with code {code}')
        else:
            logger.error(f'Failed to send SMS to {phone_number}')
            raise exceptions.VerificationCodeSentFailure(f'Failed to send SMS to {phone_number}')

    def _send_email_verification(self, email, code):
        if services.send_email([email], code):
            logger.info(f'Email sent to {email} with code {code}')
        else:
            logger.error(f'Failed to send email to {email}')
            raise exceptions.VerificationCodeSentFailure(f'Failed to send email to {email}')





class UserRegistrationVerifyPhoneSerializer(serializers.Serializer):
    """Serializer for verifying a phone number."""
    phone_number = serializers.CharField(required=True)
    code = serializers.CharField(required=True, max_length=6)

    def validate(self, attrs):
        """Validate phone number and verification code."""
        phone_number = attrs.get('phone_number')
        code = attrs.get('code')

        if not phone_number or not code:
            logger.warning('Phone verification attempt without phone number or code')
            raise serializers.ValidationError({'non_field_errors': 'Phone number and code are required.'})

        try:
            phone_verification = models.PhoneVerification.objects.get(phone_number=phone_number, code=code)
        except models.PhoneVerification.DoesNotExist:
            logger.warning(f'Invalid phone verification attempt for number: {phone_number}')
            raise serializers.ValidationError({'non_field_errors': 'Invalid phone number or code.'})

        if phone_verification.is_verified:
            logger.info(f'Attempted verification of already verified phone number: {phone_number}')
            raise serializers.ValidationError({'phone_number': 'This phone number is already verified.'})

        expiration_time = timezone.now() - timedelta(minutes=int(env.get('PHONE_NUMBER_VERIFICATION_CODE_EXPIRATION_MINUTES', 10)))
        if phone_verification.created_at < expiration_time:
            logger.warning(f'Expired verification code used for phone number: {phone_number}')
            raise serializers.ValidationError({'code': 'The verification code has expired.'})

        attrs['phone_verification'] = phone_verification
        return attrs

    def create(self, validated_data):
        """Confirm phone number verification."""
        phone_verification = validated_data['phone_verification']
        phone_verification.is_verified = True
        phone_verification.save()
        logger.info(f'Phone number verified successfully for user {phone_verification.user.id}')
        return phone_verification


class UserRegistrationResendPhoneVerificationSerializer(serializers.Serializer):
    """Serializer for resending a phone verification code."""
    phone_number = serializers.CharField(required=True)

    def validate(self, attrs):
        """Validate phone number for resending verification code."""
        phone_number = attrs.get('phone_number')

        if not phone_number:
            logger.warning('Resend verification attempt without phone number')
            raise serializers.ValidationError({'phone_number': 'Phone number is required.'})

        try:
            phone_verification = models.PhoneVerification.objects.get(phone_number=phone_number)
        except models.PhoneVerification.DoesNotExist:
            logger.warning(f'Resend verification attempt for unregistered phone number: {phone_number}')
            raise serializers.ValidationError({'phone_number': 'This phone number is not registered.'})

        if phone_verification.is_verified:
            logger.info(f'Attempted resend verification for already verified number: {phone_number}')
            raise serializers.ValidationError({'phone_number': 'This phone number is already verified.'})

        attrs['phone_verification'] = phone_verification
        return attrs

    def create(self, validated_data):
        """Resend a phone verification code."""
        phone_number = validated_data['phone_number']
        phone_verification = validated_data['phone_verification']
        phone_verification.delete()

        try:
            user = models.CustomUser.objects.get(phone_number=phone_number)
            verification_code = models.PhoneVerification.gen_code()
            new_phone_verification = models.PhoneVerification.objects.create(
                user=user,
                phone_number=phone_number,
                code=verification_code,
                is_verified=False
            )
            services.send_sms(phone_number, verification_code)
            logger.info(f'New verification code sent to phone number for user {user.id}')
            return user
        except models.CustomUser.DoesNotExist:
            logger.error(f'User not found for phone number: {phone_number}')
            raise serializers.ValidationError({'phone_number': 'User with this phone number not found.'})
        
        
class UserRegistrationVerifyEmailSerializer(serializers.Serializer):
    """Serializer for verifying a email."""
    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True, max_length=6)

    def validate(self, attrs):
        """Validate email and verification code."""
        email = attrs.get('email')
        code = attrs.get('code')

        if not email or not code:
            logger.warning('Email verification attempt without email address or code')
            raise serializers.ValidationError({'non_field_errors': 'Email and code are required.'})

        try:
            email_verification = models.EmailVerification.objects.get(email=email, code=code)
        except models.EmailVerification.DoesNotExist:
            logger.warning(f'Invalid phone verification attempt for number: {email}')
            raise serializers.ValidationError({'non_field_errors': 'Invalid email or code.'})

        if email_verification.is_verified:
            logger.info(f'Attempted verification of already verified email: {email}')
            raise serializers.ValidationError({'email': 'This email is already verified.'})

        expiration_time = timezone.now() - timedelta(minutes=int(env.get('PHONE_NUMBER_VERIFICATION_CODE_EXPIRATION_MINUTES', 10)))
        if email_verification.created_at < expiration_time:
            logger.warning(f'Expired verification code used for email: {email}')
            raise serializers.ValidationError({'code': 'The verification code has expired.'})

        attrs['email_verification'] = email_verification
        return attrs

    def create(self, validated_data):
        """Confirm email verification."""
        email_verification = validated_data['email_verification']
        email_verification.is_verified = True
        email_verification.save()
        logger.info(f'Email verified successfully for user {email_verification.user.id}')
        return email_verification
    
    
class UserRegistrationResendEmailVerificationSerializer(serializers.Serializer):
    """Serializer for resending a email code."""
    email = serializers.EmailField(required=True)

    def validate(self, attrs):
        """Validate email for resending verification code."""
        email = attrs.get('email')

        if not email:
            logger.warning('Resend verification attempt without email')
            raise serializers.ValidationError({'email': 'Email is required.'})

        try:
            email_verification = models.EmailVerification.objects.get(email=email)
        except models.PhoneVerification.DoesNotExist:
            logger.warning(f'Resend verification attempt for unregistered email: {email}')
            raise serializers.ValidationError({'email': 'This email is not registered.'})

        if email_verification.is_verified:
            logger.info(f'Attempted resend verification for already verified email: {email}')
            raise serializers.ValidationError({'email': 'This email is already verified.'})

        attrs['email_verification'] = email_verification
        return attrs

    def create(self, validated_data):
        """Resend a email verification code."""
        email = validated_data['email']
        email_verification = validated_data['email_verification']
        email_verification.delete()

        try:
            user = models.CustomUser.objects.get(email=email)
            verification_code = models.EmailVerification.gen_code()
            new_email_verification = models.EmailVerification.objects.create(
                user=user,
                email=email,
                code=verification_code,
                is_verified=False
            )
            services.send_email([email], verification_code)
            logger.info(f'New verification code sent to email for user {user.id}')
            return user
        except models.CustomUser.DoesNotExist:
            logger.error(f'User not found for email: {email}')
            raise serializers.ValidationError({'email': 'User with this email not found.'})