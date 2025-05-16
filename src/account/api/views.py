from os import environ as env
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_yasg.utils import swagger_auto_schema
from dotenv import load_dotenv
from account.api import serializers
from account.models import CustomUser
from auth.logging_config import logger


load_dotenv()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = serializers.CustomTokenObtainPairSerializer
    
    
class UserListAPIView(APIView):
    """API endpoint to retrieve a list of all users."""

    def get(self, request):
        """Handle GET requests to list all users."""
        try:
            users = CustomUser.objects.all()
            serializer = serializers.UsersListSerializer(users, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": f"Error retrieving users: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserDetailAPIView(APIView):
    """API endpoint to retrieve a detail of user."""

    def get(self, request, id):
        """Handle GET requests to get detail of user."""
        try:
            user = CustomUser.objects.filter(id=id).first()
            if not user:
                return Response(
                    {"detail": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            serializer = serializers.UsersListSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": f"Error retrieving user: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserRegisterAPIView(APIView):
    """API endpoint for user registration via email or phone number."""

    @swagger_auto_schema(
        request_body=serializers.UserRegisterSerializer,
        responses={
            201: serializers.UserRegisterSerializer,
            400: "Bad Request",
            500: "Internal Server Error",
        },
        operation_description="Register a new user with email or phone number. Sends a verification code if phone number is provided.",
        tags=['registration']
    )
    def post(self, request):
        """Handle POST requests to register a new user."""
        serializer = serializers.UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                response_data = {
                    "detail": "Verification code sent successfully",
                    "expiration_time_in_minutes": int(env.get('PHONE_NUMBER_VERIFICATION_CODE_EXPIRATION_MINUTES', 10)),
                }
                return Response(response_data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    {"detail": f"Error during registration: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRegistrationVerifyPhoneAPIView(APIView):
    """API endpoint to verify a phone number with a code."""

    @swagger_auto_schema(
        request_body=serializers.UserRegistrationVerifyPhoneSerializer,
        responses={
            200: "Phone number verified",
            400: "Bad Request",
            500: "Internal Server Error",
        },
        operation_description="Verify a phone number using the provided verification code.",
        tags=['verification-phone']
    )
    def post(self, request):
        """Handle POST requests to verify a phone number."""
        serializer = serializers.UserRegistrationVerifyPhoneSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(
                    {"detail": "Phone number verified successfully"},
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                return Response(
                    {"detail": f"Error verifying phone number: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRegistrationResendVerificationPhoneAPIView(APIView):
    """API endpoint to resend a verification code to an unverified phone number."""

    @swagger_auto_schema(
        request_body=serializers.UserRegistrationResendPhoneVerificationSerializer,
        responses={
            201: "Verification code resent",
            400: "Bad Request",
            500: "Internal Server Error",
        },
        operation_description="Resend a verification code to an unverified phone number.",
        tags=['verification-phone']
    )
    def post(self, request):
        """Handle POST requests to resend a phone verification code."""
        serializer = serializers.UserRegistrationResendPhoneVerificationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                response_data = {
                    "detail": "Verification code resent successfully",
                    "expiration_time_in_minutes": int(env.get('PHONE_NUMBER_VERIFICATION_CODE_EXPIRATION_MINUTES', 10))
                }
                logger.info(f"Successfully resent verification code")
                return Response(response_data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error resending verification code: {str(e)}")
                return Response(
                    {"detail": f"Error resending verification code: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        logger.warning("Invalid resend verification data received")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class UserRegistrationVerifyEmailAPIView(APIView):
    """API endpoint to verify a email with a code."""

    @swagger_auto_schema(
        request_body=serializers.UserRegistrationVerifyEmailSerializer,
        responses={
            200: "Email verified",
            400: "Bad Request",
            500: "Internal Server Error",
        },
        operation_description="Verify a email using the provided verification code.",
        tags=['verification-email']
    )
    def post(self, request):
        """Handle POST requests to verify a email."""
        serializer = serializers.UserRegistrationVerifyEmailSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(
                    {"detail": "Email verified successfully"},
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                return Response(
                    {"detail": f"Error verifying email: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class UserRegistrationResendVerificationEmailAPIView(APIView):
    """API endpoint to resend a verification code to an unverified email."""

    @swagger_auto_schema(
        request_body=serializers.UserRegistrationResendEmailVerificationSerializer,
        responses={
            201: "Verification code resent",
            400: "Bad Request",
            500: "Internal Server Error",
        },
        operation_description="Resend a verification code to an unverified email.",
        tags=['verification-email']
    )
    def post(self, request):
        """Handle POST requests to resend a email verification code."""
        serializer = serializers.UserRegistrationResendEmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                response_data = {
                    "detail": "Verification code resent successfully",
                    "expiration_time_in_minutes": int(env.get('PHONE_NUMBER_VERIFICATION_CODE_EXPIRATION_MINUTES', 10))
                }
                logger.info(f"Successfully resent verification code")
                return Response(response_data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error resending verification code: {str(e)}")
                return Response(
                    {"detail": f"Error resending verification code: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        logger.warning("Invalid resend verification data received")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)