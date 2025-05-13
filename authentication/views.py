import requests
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import action
import random
from django.core.cache import cache
from rest_framework import status
from django.contrib.auth import login
from datetime import datetime, timedelta
from django.utils.translation import gettext as _
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.parsers import MultiPartParser, FormParser
from konkurs.serializers import PersonalInfoSerializer
from .models import User, SMSCode, BlacklistedAccessToken
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
    ResetPasswordSerializer, LogoutSerializer, SetProfileSerializer, RegisterSerializers
)
from .validators import validate_uz_phone_number
from .utils import send_message_telegram


class RegistrationViewSet(ViewSet):
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
        serializer = SetPasswordSerializer(data=request.data, context={'request': request})
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
        serializer = PersonalInfoSerializer(user, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Foydalanuvchini ro'yxatdan o'tkazish va OTP kod yuborish",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="Telefon raqam"),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description="Ism"),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description="Familiya"),
                'middle_name': openapi.Schema(type=openapi.TYPE_STRING, description="Otasi ismi"),
                'birth_date': openapi.Schema(type=openapi.FORMAT_DATE, description="Tug'ilgan sana"),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description="Email"),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description="Parol"),
                'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, description="Parolni tasdiqlash"),
            },
            required=['phone_number', 'first_name', 'last_name', 'password', 'confirm_password']
        ),
        responses={
            200: openapi.Response(description="OTP kod yuborildi"),
            400: openapi.Response(description="Parollar mos emas yoki foydalanuvchi allaqachon mavjud"),
            500: openapi.Response(description="OTP yuborishda xato yuz berdi")
        }
    )
    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        phone_number = request.data.get('phone_number')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        middle_name = request.data.get('middle_name')
        birth_date = request.data.get('birth_date')
        email = request.data.get('email')
        password = request.data.get('password')
        serializer = RegisterSerializers(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        otp_code = random.randint(100000, 999999)

        cache.set(f'register_{phone_number}', {
            'first_name': first_name,
            'last_name': last_name,
            'middle_name': middle_name,
            'birth_date': birth_date,
            'email': email,
            'password': password,
        }, timeout=300)

        cache.set(f'otp_{phone_number}', otp_code, timeout=300)

        response = send_message_telegram(phone_number, otp_code)
        if response.status_code != 200:
            return Response({'error': _('OTP yuborishda xato yuz berdi')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'message': _('OTP kod yuborildi')}, status=status.HTTP_200_OK)

class OTPVerificationViewSet(ViewSet):
    @swagger_auto_schema(
        operation_description="OTP kodini tekshirish va foydalanuvchini yaratish",
        operation_summary="Verify Otp",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="Telefon raqam"),
                'otp_code': openapi.Schema(type=openapi.TYPE_STRING, description="OTP kod"),
            },
            required=['phone_number', 'otp_code']
        ),
        responses={
            201: openapi.Response(description="Ro‘yxatdan o‘tish muvaffaqiyatli yakunlandi"),
            400: openapi.Response(description="Kiritilgan kod noto‘g‘ri yoki muddati o‘tgan"),
            500: openapi.Response(description="Foydalanuvchini yaratishda xato")
        }
    )
    @action(detail=False, methods=['post'], url_path='verify')
    def verify(self, request):
        phone_number = request.data.get('phone_number')
        otp_code = request.data.get('otp_code')

        cached_otp = cache.get(f'otp_{phone_number}')

        if cached_otp and str(cached_otp) == otp_code:
            user_data = cache.get(f'register_{phone_number}')

            if user_data:
                try:
                    user = User.objects.create_user(
                        phone_number=phone_number,
                        first_name=user_data.get('first_name'),
                        last_name=user_data.get('last_name'),
                        middle_name=user_data.get('middle_name'),
                        birth_date=user_data.get('birth_date'),
                        email=user_data.get('email'),
                        password=user_data.get('password'),
                    )
                    user.is_active = True
                    user.role = 1
                    user.save()

                    cache.delete(f'otp_{phone_number}')
                    cache.delete(f'register_{phone_number}')

                    return Response({'message': _('Ro‘yxatdan o‘tish muvaffaqiyatli yakunlandi')},
                                    status=status.HTTP_201_CREATED)
                except Exception as e:
                    return Response({'error': _("Foydalanuvchini yaratishda xato: %(error)s") % {'error': str(e)}},
                                    status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': _('Kiritilgan kod noto‘g‘ri yoki muddati o‘tgan')},
                        status=status.HTTP_400_BAD_REQUEST)


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
        serializer = SendTempPasswordSerializer(data=request.data, context={'request': request})
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
        serializer = ResetPasswordSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response({"message": _("Password reset successfully.")}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh_token': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token'),
                'access_token': openapi.Schema(type=openapi.TYPE_STRING, description='Access_token')
            }
        ),
        responses={
            205: 'Token has been added to blacklist',
            400: 'Refresh token not provided'
        },
        operation_summary="User logout",
        operation_description="This endpoint allows a user to log out."
    )
    def logout(self, request):
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={'error': serializer.errors, 'ok': False}, status=status.HTTP_400_BAD_REQUEST)
        refresh_token = serializer.validated_data['refresh_token']
        access_token = serializer.validated_data['access_token']
        token1 = RefreshToken(refresh_token)
        token2 = AccessToken(access_token)
        token1.blacklist()
        obj = BlacklistedAccessToken.objects.create(token=token2)
        obj.save()
        return Response({'message': _('Logged out successfully'), 'ok': True},
                        status=status.HTTP_205_RESET_CONTENT)


class PersonalInfoViewSet(ViewSet):
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Get Exist Personal Info",
        operation_summary="Get Exist Personal Info",
        responses={200: SetProfileSerializer()},
        tags=['auth'],
    )
    def get_exist_personal_info(self, request, *args, **kwargs):
        user_info = User.objects.filter(id=kwargs['pk']).first()
        if user_info is None:
            return Response(data={'error': _('User not found')}, status=status.HTTP_404_NOT_FOUND)
        serializer = SetProfileSerializer(user_info)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Personal Info",
        operation_summary="Personal Info",
        manual_parameters=[
            openapi.Parameter(
                name='first_name',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="first_name"
            ),
            openapi.Parameter(
                name='last_name',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="last_name",
            ),
            openapi.Parameter(
                name='middle_name',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="middle_name",
            ),
            openapi.Parameter(
                name='birth_date',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="birth_date",
            ),
            openapi.Parameter(
                name='phone_number',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="phone_number",
            ),
            openapi.Parameter(
                name='email',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="email",
            ),
            openapi.Parameter(
                name='image',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=False,
                description="image",
            ),
        ],
        responses={200: SetProfileSerializer()},
        tags=['auth'],
    )
    def personal_info(self, request, *args, **kwargs):
        user_id = request.user.id
        user_info = User.objects.filter(id=user_id).first()
        if user_info is None:
            return Response(data={'error': _('unauthorized')}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = SetProfileSerializer(user_info, data=request.data, patial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    # @swagger_auto_schema(
    #     operation_description="Create Jury",
    #     operation_summary="Create Jury",
    #     request_body=openapi.Schema(
    #         type=openapi.TYPE_OBJECT,
    #         properties={
    #             'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='first_name'),
    #             'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='last_name'),
    #             'middle_name': openapi.Schema(type=openapi.TYPE_STRING, description='middle_name'),
    #             'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='phone_number'),
    #             'birth_date': openapi.Schema(type=openapi.TYPE_STRING, description='birth_date'),
    #             'email': openapi.Schema(type=openapi.TYPE_STRING, description='email'),
    #             'password': openapi.Schema(type=openapi.TYPE_STRING, description='password'),
    #             'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, description='confirm_password'),
    #         },
    #         required=['first_name', 'last_name', 'middle_name', 'birth_date', 'phone_number', 'email',
    #                   'password', 'confirm_password']
    #     ),
    #     responses={201: RegisterSerializers()},
    #     tags=['auth'],
    # )
    # def register(self, request, *args, **kwargs):
    #     serializer = RegisterSerializers(data=request.data)
    #     if not serializer.is_valid():
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #     print('=' * 100)
    #     print(serializer.data)
    #     print('=' * 100)
    #     return Response(data=serializer.data, status=status.HTTP_200_OK)
    #
    # def verify_otp_code(self, request, *args, **kwargs):
    #     pass


class ForgotPasswordViewSet(ViewSet):

    @swagger_auto_schema(
        operation_description="Parolni tiklash uchun OTP kod yuborish",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="Telefon raqam"),
            },
            required=['phone_number']
        ),
        responses={
            200: openapi.Response(description="OTP kod yuborildi"),
            400: openapi.Response(description="Foydalanuvchi topilmadi yoki OTP yuborishda xato yuz berdi"),
        }
    )
    @action(detail=False, methods=['post'], url_path='forgot-password')
    def forgot_password(self, request):
        phone_number = request.data.get('phone_number')

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({'error': _('Telefon raqam tizimda mavjud emas')}, status=status.HTTP_400_BAD_REQUEST)

        otp_code = random.randint(100000, 999999)

        cache.set(f'forgot_otp_{phone_number}', otp_code, timeout=300)

        response = send_message_telegram(phone_number, otp_code)
        if response.status_code != 200:
            return Response({'error': _('OTP yuborishda xato yuz berdi')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'message': _('OTP kod yuborildi')}, status=status.HTTP_200_OK)


class ResetPasswordViewSet(ViewSet):
    @swagger_auto_schema(
        operation_description="Parolni tiklash uchun OTP kodni tasdiqlash va yangi parolni o'rnatish",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="Telefon raqam"),
                'otp_code': openapi.Schema(type=openapi.TYPE_STRING, description="OTP kod"),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description="Yangi parol"),
                'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, description="Yangi parolni tasdiqlash"),
            },
            required=['phone_number', 'otp_code', 'new_password', 'confirm_password']
        ),
        responses={
            200: openapi.Response(description="Parol muvaffaqiyatli o'zgartirildi"),
            400: openapi.Response(description="Kod noto‘g‘ri yoki muddati o‘tgan yoki parollar mos emas"),
        }
    )
    @action(detail=False, methods=['post'], url_path='reset-password')
    def reset_password(self, request):
        phone_number = request.data.get('phone_number')
        otp_code = request.data.get('otp_code')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        cached_otp = cache.get(f'forgot_otp_{phone_number}')

        if cached_otp and str(cached_otp) == otp_code:
            if new_password != confirm_password:
                return Response({'error': _('Parollar mos emas')}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(phone_number=phone_number)
                user.set_password(new_password)
                user.save()

                cache.delete(f'forgot_otp_{phone_number}')

                return Response({'message': _('Parol muvaffaqiyatli o‘zgartirildi')}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'error': _('Foydalanuvchi topilmadi')}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': _('Kod noto‘g‘ri yoki muddati o‘tgan')}, status=status.HTTP_400_BAD_REQUEST)
