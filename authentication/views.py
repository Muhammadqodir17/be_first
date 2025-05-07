import requests
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from django.contrib.auth import login
from datetime import datetime, timedelta
from django.utils.translation import gettext as _
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from konkurs.serializers import PersonalInfoSerializer
from .models import User, SMSCode
from .validators import validate_uz_phone_number
from django.utils.crypto import get_random_string
from rest_framework_simplejwt.tokens import (
    AccessToken,
    RefreshToken
)
from .serializers import (
    UserSerializer,
    SendSMSSerializer,
    VerifySMSSerializer,
    SetPasswordSerializer,
    LoginSerializer,
    SendTempPasswordSerializer,
    ResetPasswordSerializer
)
from .validators import validate_uz_phone_number

BOT_TOKEN = '7662698791:AAFF7tOLoXxRhLIwL5ltuEuxpsyqIm4UUKE'
CHAT_ID = '-4777486427'


class RegistrationViewSet(ViewSet):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The phone number to send the SMS to.",
                    example="+1234567890"
                )
            },
            required=['phone_number'],
        ),
        responses={
            200: openapi.Response(
                description="SMS sent successfully.",
                examples={
                    "application/json": {"message": "SMS-code sent."}
                }
            ),
            400: openapi.Response(
                description="Error occurred.",
                examples={
                    "application/json": {"error": "Failed to send message"}
                }
            ),
        },
        operation_summary="Send SMS verification code",
        operation_description="Sends a 6-digit verification code to the provided phone number."
    )
    def send_sms(self, request):
        serializer = SendSMSSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data['phone_number']
        sms = SMSCode.objects.filter(phone_number=phone_number, expires_at__gt=datetime.now()).first()

        code = get_random_string(length=6, allowed_chars='0123456789')
        SMSCode.objects.create(phone_number=phone_number, code=code, expires_at=datetime.now() + timedelta(minutes=5))

        message = _("Your verification code is: %(code)s") % {'code': code}
        telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
        response = requests.get(telegram_url)

        if response.status_code == 200:
            return Response({"message": _("SMS-code sent.")}, status=status.HTTP_200_OK)
        else:
            return Response({"error": _("Failed to send message")}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The phone number associated with the SMS code.",
                    example="+1234567890"
                ),
                'sms_code': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The 6-digit SMS code received by the user.",
                    example="123456"
                ),
            },
            required=['phone_number', 'sms_code'],
        ),
        responses={
            200: openapi.Response(
                description="Code verified successfully, and access token is returned.",
                examples={
                    "application/json": {
                        "message": "Code verified.",
                        "access_token": "eyJhbGciOiJIUzI1..."
                    }
                }
            ),
            400: openapi.Response(
                description="Incorrect or expired code, or invalid request data.",
                examples={
                    "application/json": {
                        "error": "Incorrect or expired code."
                    }
                }
            ),
        },
        operation_summary="Verify SMS code",
        operation_description=(
                "Verifies the SMS code sent to the user's phone number. "
                "If valid, marks the code as verified and returns an access token."
        )
    )
    def verify_sms(self, request):
        serializer = VerifySMSSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data['phone_number']
        code = serializer.validated_data['sms_code']

        sms_code = SMSCode.objects.filter(
            phone_number=phone_number,
            code=code,
            expires_at__gt=datetime.now()
        ).first()

        if sms_code is None:
            return Response(data={"error": _("Incorrect or expired code.")}, status=status.HTTP_400_BAD_REQUEST)

        sms_code.verified = True
        sms_code.save()

        user = User.objects.get_or_create(phone_number=phone_number)
        user.role = 1
        user.save()
        token = AccessToken.for_user(user)

        return Response(
            {"message": _("Code verified."), "access_token": f'{str(token)}'},
            status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The phone number of the user.",
                    example="+998123456789"
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The new password to set.",
                    example="securepassword123"
                ),
                'confirm_password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Confirmation of the new password.",
                    example="securepassword123"
                ),
            },
            required=['phone_number', 'password', 'confirm_password'],
        ),
        responses={
            200: openapi.Response(
                description="Password set successfully.",
                examples={
                    "application/json": {
                        "message": "Password set."
                    }
                }
            ),
            400: openapi.Response(
                description="Invalid input data.",
                examples={
                    "application/json": {
                        "phone_number": ["This field is required."],
                        "password": ["This field is required."],
                        "confirm_password": ["Passwords do not match."]
                    }
                }
            ),
        },
        operation_summary="Set a new password",
        operation_description=(
                "Allows a user to set a new password for their account. The request must include the "
                "user's phone number, the new password, and a confirmation of the password."
        )
    )
    def set_password(self, request):
        serializer = SetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response({"message": _("Password set.")}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get user",
        operation_summary="Get user",
        responses={
            200: PersonalInfoSerializer(),
        },
        tags=['auth']
    )
    def get_user(self, request, *args, **kwargs):
        user = User.objects.filter(id=request.user.id).first()
        if user is None:
            return Response(data={'error': _('User not found')}, status=status.HTTP_404_NOT_FOUND)
        serializer = PersonalInfoSerializer(user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The user's phone number.",
                    example="+1234567890"
                ),
                'first_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The user's first name.",
                    example="John"
                ),
                'last_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The user's last name.",
                    example="Doe"
                ),
                'middle_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The user's middle name.",
                    example="Michael"
                ),
                'birth_date': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="date",
                    description="The user's birth date in YYYY-MM-DD format.",
                    example="1990-01-01"
                ),
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="email",
                    description="The user's email address.",
                    example="john.doe@example.com"
                ),
            },
            required=['phone_number', 'first_name', 'last_name', 'middle_name', 'birth_date', 'email'],
        ),
        responses={
            200: openapi.Response(
                description="Profile updated successfully.",
                examples={
                    "application/json": {
                        "message": "Personal data saved.",
                        "data": {
                            "phone_number": "+1234567890",
                            "first_name": "John",
                            "last_name": "Doe",
                            "middle_name": "Michael",
                            "birth_date": "1990-01-01",
                            "email": "john.doe@example.com"
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request. Missing or invalid fields.",
                examples={
                    "application/json": {"message": "First name is required."}
                }
            ),
            404: openapi.Response(
                description="User not found.",
                examples={
                    "application/json": {"error": "User not found."}
                }
            ),
        },
        operation_summary="Update user profile",
        operation_description=(
                "Updates the user's profile information. All fields are required, and the user is identified by the phone number."
        )
    )
    def set_profile(self, request):
        phone_number = request.data.get('phone_number')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        middle_name = request.data.get('middle_name')
        birth_date = request.data.get('birth_date')
        email = request.data.get('email')
        if not phone_number:
            return Response({"message": _("Phone number is required.")}, status=status.HTTP_400_BAD_REQUEST)
        if not first_name:
            return Response({"message": _("First name is required.")}, status=status.HTTP_400_BAD_REQUEST)
        if not last_name:
            return Response({"message": _("Last name is required.")}, status=status.HTTP_400_BAD_REQUEST)
        if not middle_name:
            return Response({"message": _("Middle name is required.")}, status=status.HTTP_400_BAD_REQUEST)
        if not birth_date:
            return Response({'message': _('Birth date is required.')}, status=status.HTTP_400_BAD_REQUEST)
        if not email:
            return Response({'message': _('Email is required.')}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({"error": _("User not found.")}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": _("Personal data saved."), "data": serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginViewSet(ViewSet):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The username or email of the user.",
                    example="john_doe"
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The user's password.",
                    example="securepassword123"
                ),
            },
            required=['username', 'password'],
        ),
        responses={
            200: openapi.Response(
                description="User login successful.",
                examples={
                    "application/json": {
                        "message": "User login success."
                    }
                }
            ),
            400: openapi.Response(
                description="Invalid input data.",
                examples={
                    "application/json": {
                        "username": ["This field is required."],
                        "password": ["This field is required."]
                    }
                }
            ),
        },
        operation_summary="Log in a user",
        operation_description=(
                "Allows a user to log in by providing their username (or email) and password. "
                "If the credentials are valid, the user is authenticated and logged in."
        )
    )
    def login_user(self, request):
        data = request.data

        if '+' in data.get('username'):
            phone_number = data.get('username')
            validate_uz_phone_number(phone_number)
            user = User.objects.filter(phone_number=phone_number).first()
            if user is None:
                return Response({'message': _('User not found.')}, status=status.HTTP_404_NOT_FOUND)
        else:
            user = User.objects.filter(username=data.get('username')).first()
            if user is None:
                return Response({'message': _('User not found.')}, status=status.HTTP_404_NOT_FOUND)
        if not user.check_password(data.get('password')):
            return Response(data={'error': _('Password is incorrect')}, status=status.HTTP_400_BAD_REQUEST)
        refresh_token = RefreshToken.for_user(user)
        access_token = refresh_token.access_token
        access_token['role'] = user.role

        return Response(data={'refresh': str(refresh_token), 'access_token': str(access_token)},
                        status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The phone number of the user to send the temporary password.",
                    example="+1234567890"
                ),
            },
            required=['phone_number'],
        ),
        responses={
            200: openapi.Response(
                description="Temporary password sent successfully.",
                examples={
                    "application/json": {
                        "message": "Temp password sent."
                    }
                }
            ),
            400: openapi.Response(
                description="Invalid input data.",
                examples={
                    "application/json": {
                        "phone_number": ["This field is required."]
                    }
                }
            ),
        },
        operation_summary="Send Temporary Password",
        operation_description=(
                "This endpoint allows a user to request a temporary password by providing their phone number. "
                "The temporary password will be sent to the specified phone number."
        )
    )
    def send_temp_password(self, request):
        serializer = SendTempPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response({'message': _('Temp password sent.')}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The phone number associated with the user's account.",
                    example="+1234567890"
                ),
                'temp_password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The temporary password sent to the user's phone number.",
                    example="123456"
                ),
                'new_password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The new password to set for the account.",
                    example="secureNewPassword123"
                ),
            },
            required=['phone_number', 'temp_password', 'new_password'],
        ),
        responses={
            200: openapi.Response(
                description="Password reset successfully.",
                examples={
                    "application/json": {
                        "message": "Password reset successfully."
                    }
                }
            ),
            400: openapi.Response(
                description="Invalid input data.",
                examples={
                    "application/json": {
                        "phone_number": ["This field is required."],
                        "temp_password": ["This field is required."],
                        "new_password": ["This field is required."]
                    }
                }
            ),
        },
        operation_summary="Reset Password",
        operation_description=(
                "This endpoint allows users to reset their password by providing their phone number, a temporary password, "
                "and a new password. The temporary password must be valid for the operation to succeed."
        )
    )
    def reset_password(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response({"message": _("Password reset successfully.")}, status=status.HTTP_200_OK)
