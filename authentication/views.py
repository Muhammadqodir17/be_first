import requests
from django.contrib.auth.hashers import make_password
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
from .models import User, SMSCode, BlacklistedAccessToken, OTPRegisterResend, OTPSetPassword
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
    LoginSerializer,
    SendTempPasswordSerializer,
    ResetPasswordSerializer,
    LogoutSerializer,
    SetProfileSerializer,
    RegisterSerializers,
    ChangePasswordSerializer,
    SetPasswordSerializer, ReSetPassSerializer, TestSerializer
)
from .validators import validate_uz_phone_number
from .utils import send_message_telegram, checking_number_of_otp, check_code_expire, check_token_expire, \
    check_resend_otp_code, send_message_to_telegram


class RegistrationViewSet(ViewSet):
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

        response = send_message_to_telegram(phone_number, otp_code)
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
                'type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Qaysi holat uchun: 'register' yoki 'forgot'",
                    enum=['register', 'forgot'])
            },
            required=['phone_number', 'otp_code']
        ),
        responses={
            201: openapi.Response(description="Ro‘yxatdan o‘tish muvaffaqiyatli yakunlandi"),
            400: openapi.Response(description="Kiritilgan kod noto‘g‘ri yoki muddati o‘tgan"),
            500: openapi.Response(description="Foydalanuvchini yaratishda xato")
        }
    )
    def verify(self, request):
        phone_number = request.data.get('phone_number')
        user = User.objects.filter(phone_number=phone_number).first()
        otp_code = request.data.get('otp_code')
        f_type = request.data.get('type')

        if f_type not in ['register', 'forgot']:
            return Response({'error': _('Noto‘g‘ri type')}, status=status.HTTP_400_BAD_REQUEST)

        if f_type == 'register':
            register = cache.get(f'otp_{phone_number}')
            if not register:
                return Response({'error': _('Kiritilgan kod muddati o‘tgan')},
                                status=status.HTTP_400_BAD_REQUEST)
            if str(register) == otp_code:
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
                        user.type = 2
                        user.save()

                        cache.delete(f'otp_{phone_number}')
                        cache.delete(f'register_{phone_number}')

                        refresh_token = RefreshToken.for_user(user)
                        access_token = refresh_token.access_token
                        access_token['role'] = user.role

                        return Response(
                            data={'refresh': str(refresh_token), 'access_token': str(access_token), 'type': 'register'},
                            status=status.HTTP_200_OK)
                    except Exception as e:
                        return Response({'error': _("Foydalanuvchini yaratishda xato: %(error)s") % {'error': str(e)}},
                                        status=status.HTTP_400_BAD_REQUEST)
            return Response({'error': _('Kiritilgan kod noto‘g‘ri')},
                            status=status.HTTP_400_BAD_REQUEST)

        elif f_type == 'forgot':
            forgot = cache.get(f'forgot_otp_{phone_number}')
            if not forgot:
                return Response({'error': _('Kiritilgan kod muddati o‘tgan')},
                                status=status.HTTP_400_BAD_REQUEST)
            if str(forgot) == otp_code:
                user.is_verified = True
                user.type = 1
                user.save()
                return Response(data={'verified': phone_number, 'type': 'forgot'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': _('Kiritilgan kod noto‘g‘ri')},
                                status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Create Category",
        operation_summary="Create Category",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='phone_number'),
                'type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Qaysi holat uchun: 'register' yoki 'forgot'",
                    enum=['register', 'forgot']
                ),
            },
            required=['phone_number']
        ),
        responses={200: 'OTP kod yuborildi',
                   400: 'OTP yuborishda xato yuz berdi'},
        tags=['auth'],
    )
    def resend_otp(self, request, *args, **kwargs):
        phone_number = request.data['phone_number']
        user = User.objects.filter(phone_number=phone_number).first()
        if user is None:
            return Response(data={'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        otp_code = random.randint(100000, 999999)
        f_type = request.data.get('type')
        if f_type == 'register':
            cache.set(f'otp_{phone_number}', otp_code, timeout=300)
        else:
            cache.set(f'forgot_otp_{phone_number}', otp_code, timeout=300)
        response = send_message_to_telegram(phone_number, otp_code)
        if response.status_code != 200:
            return Response({'error': _('OTP yuborishda xato yuz berdi')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'message': _('OTP kod yuborildi')}, status=status.HTTP_200_OK)


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
        serializer = SetProfileSerializer(user_info, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)


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
    def forgot_password(self, request):
        phone_number = request.data.get('phone_number')
        user = User.objects.filter(phone_number=phone_number).first()
        if user is None:
            return Response(data={'error': 'User with this phone number not found'}, status=status.HTTP_404_NOT_FOUND)
        otp_code = random.randint(100000, 999999)
        cache.set(f'forgot_otp_{phone_number}', otp_code, timeout=300)
        response = send_message_to_telegram(phone_number, otp_code)
        if response.status_code != 200:
            return Response({'error': _('OTP yuborishda xato yuz berdi')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'message': _('OTP kod yuborildi')}, status=status.HTTP_200_OK)


class ResetPasswordViewSet(ViewSet):
    @swagger_auto_schema(
        operation_description="Set Password",
        operation_summary="Set Password",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'old_password': openapi.Schema(type=openapi.TYPE_STRING, description='old_password'),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='new_password'),
                'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, description='confirm_password'),
            },
            required=['old_password', 'new_password', 'confirm_password']
        ),
        responses={200: 'Password set.'},
        tags=['auth'],
    )
    def set_pass(self, request, *args, **kwargs):
        serializer = SetPasswordSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data={'message': _("Password set.")}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="ReSet Password",
        operation_summary="ReSet Password",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='phone_number'),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='new_password'),
                'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, description='confirm_password'),
            },
            required=['new_password', 'confirm_password', 'phone_number']
        ),
        responses={200: 'Password reseted.'},
        tags=['auth'],
    )
    def reset_pass(self, request, *args, **kwargs):
        # user = User.objects.filter(phone_number=request.data['phone_number']).first()
        # if user is None:
        #     return Response(data={'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        # if not user.is_verified:
        #     return Response(data={'error': 'User not verified'}, status=status.HTTP_400_BAD_REQUEST)
        # serializer = ReSetPassSerializer(data=request.data)
        # if not serializer.is_valid():
        #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # serializer.validated_data['is_verified'] = False
        # serializer.save()
        # return Response(data={'message': _("Password reseted.")}, status=status.HTTP_200_OK)
        pass


class TestViewSet(ViewSet):
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
            required=['phone_number', 'birth_date', 'middle_name', 'first_name', 'last_name', 'password', 'email',
                      'confirm_password']
        ),
        responses={
            200: openapi.Response(description="OTP kod yuborildi"),
            400: openapi.Response(description="Parollar mos emas yoki foydalanuvchi allaqachon mavjud"),
            500: openapi.Response(description="OTP yuborishda xato yuz berdi")
        }
    )
    def register(self, request, *args, **kwargs):  # register
        serializer = RegisterSerializers(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.validated_data['is_active'] = False
        serializer.save()

        objs = OTPRegisterResend.objects.filter(otp_user=serializer.instance, otp_type=1, deleted_at=None).order_by(
            '-created_at')

        if not checking_number_of_otp(objs):
            return Response(data={"error": "Try again 12 hours later"}, status=status.HTTP_400_BAD_REQUEST)

        if checking_number_of_otp(objs) == 'delete':
            objs = OTPRegisterResend.objects.filter(otp_user=serializer.instance, otp_type=1, deleted_at=None)
            for obj in objs:
                obj.deleted_at = datetime.now()
                obj.save(update_fields=['deleted_at'])

        otp = OTPRegisterResend.objects.create(otp_user=serializer.instance)
        otp.save()

        response = send_message_telegram(otp)
        if response.status_code != 200:
            otp.delete()
            return Response(data={"error": "Error occured while sending otp code"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data={"otp_key": otp.otp_key, 'type': 'register', 'message': 'Otp successfully send'}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="OTP kodini tekshirish va foydalanuvchini yaratish",
        operation_summary="Verify Otp",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'otp_key': openapi.Schema(type=openapi.TYPE_STRING, description="Telefon raqam"),
                'otp_code': openapi.Schema(type=openapi.TYPE_INTEGER, description="OTP kod"),
            },
            required=['otp_key', 'otp_code']
        ),
        responses={
            201: openapi.Response(description="Ro‘yxatdan o‘tish muvaffaqiyatli yakunlandi"),
            400: openapi.Response(description="Kiritilgan kod noto‘g‘ri yoki muddati o‘tgan"),
            500: openapi.Response(description="Foydalanuvchini yaratishda xato")
        }
    )
    def verify_register(self, request, *args, **kwargs):
        otp_key = request.data.get('otp_key')
        otp_code = request.data.get('otp_code')
        if request.user.is_active:
            return Response(data={"detail": "U already verified"}, status=status.HTTP_400_BAD_REQUEST)
        if not otp_code:
            return Response(data={"error": "Send otp code"}, status=status.HTTP_400_BAD_REQUEST)
        otp_obj = OTPRegisterResend.objects.filter(otp_key=otp_key, deleted_at=None).first()
        if otp_obj is None:
            return Response(data={"error": "Make sure otp key is right"}, status=status.HTTP_400_BAD_REQUEST)
        if otp_obj.attempts > 2:
            return Response(data={"error": "Come back 12 hours later"}, status=status.HTTP_400_BAD_REQUEST)
        if otp_obj.otp_code != otp_code:
            otp_obj.attempts += 1
            otp_obj.save(update_fields=['attempts'])
            return Response(data={"error": "otp code is wrong"}, status=status.HTTP_400_BAD_REQUEST)

        if not check_code_expire(otp_obj.created_at):
            return Response(data={"error": "Code is expired"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(id=otp_obj.otp_user.id).first()
        if not user:
            return Response(data={"error": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)

        user.is_active = True
        user.save(update_fields=['is_active'])
        objs = OTPRegisterResend.objects.filter(otp_user=user, deleted_at=None)
        for obj in objs:
            obj.deleted_at = datetime.now()
            obj.save(update_fields=['deleted_at'])
        refresh_token = RefreshToken.for_user(user)
        access_token = refresh_token.access_token
        access_token['role'] = user.role
        return Response(
            data={"message": "Success", 'refresh_token': str(refresh_token), 'access_token': str(access_token)},
            status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Forgot password",
        operation_summary="Forgot password",
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
    def forgot_password(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        user = User.objects.filter(phone_number=phone_number).first()
        if not user:
            return Response(data={"error": "User not found with this number!!!"}, status=status.HTTP_404_NOT_FOUND)
        otp_obj = OTPSetPassword.objects.create(otp_user=user)
        otp_obj.save()
        response = send_message_telegram(otp_obj)
        if response.status_code != 200:
            otp_obj.deleted_at = datetime.now()
            otp_obj.save(update_fields=['deleted_at'])
            return Response({"error": "Error occured while sending otp"}, status.HTTP_400_BAD_REQUEST)
        return Response(data={"otp_key": otp_obj.otp_key, 'type': 'forgot'}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Verify forgot password",
        operation_summary="Verify forgot password",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'otp_key': openapi.Schema(type=openapi.TYPE_STRING, description="Telefon raqam"),
                'otp_code': openapi.Schema(type=openapi.TYPE_INTEGER, description="OTP kod"),
            },
            required=['otp_key', 'otp_code']
        ),
        responses={
            201: openapi.Response(description="Otp verified"),
            400: openapi.Response(description="Something went wrong"),
        }
    )
    def verify_forgot_password(self, request, *args, **kwargs):
        otp_key = request.data.get('otp_key')
        otp_code = request.data.get('otp_code')

        otp_obj = OTPSetPassword.objects.filter(otp_key=otp_key, deleted_at=None).first()
        if not otp_obj:
            return Response(data={"Error": "Otp key is wrong"}, status=status.HTTP_400_BAD_REQUEST)
        if otp_obj.attempts > 2:
            return Response(data={"error": "Try again 12 hours later"}, status=status.HTTP_400_BAD_REQUEST)
        if otp_obj.otp_code != otp_code:
            otp_obj.attempts += 1
            otp_obj.save(update_fields=['attempts'])
            return Response(data={"error": "Otp code is wrong"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data={"message": "Success", "token": otp_obj.otp_token}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="ReSet Password",
        operation_summary="ReSet Password",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'otp_token': openapi.Schema(type=openapi.TYPE_STRING, description='otp_token'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='password'),
                'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, description='confirm_password'),
            },
            required=['password', 'confirm_password', 'otp_token']
        ),
        responses={200: 'Password reseted.'},
        tags=['auth'],
    )
    def reset_password(self, request, *args, **kwargs):
        token = request.data.get('otp_token')
        obj = OTPSetPassword.objects.filter(otp_token=token, deleted_at=None).first()
        if not obj:
            return Response(data={"error": "Otp token is wrong"}, status=status.HTTP_400_BAD_REQUEST)

        if not check_token_expire(obj.created_at):
            return Response(data={"error": "Token is expired"}, status=status.HTTP_400_BAD_REQUEST)

        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')

        if password != confirm_password:
            return Response(data={"error": "Password do not match!"}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(id=obj.otp_user.id).first()
        if not user:
            return Response(data={"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = TestSerializer(user, data={'password': password}, partial=True)
        if serializer.is_valid():
            serializer.save()
            obj.deleted_at = datetime.now()
            obj.save(update_fields=['deleted_at'])
            return Response(data={"detail": "success"}, status=status.HTTP_200_OK)
        return Response(data={"error": "Please enter a valid password"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Resend Otp",
        operation_summary="Resend Otp",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'otp_key': openapi.Schema(type=openapi.TYPE_STRING, description="Telefon raqam"),
                'type': openapi.Schema(type=openapi.TYPE_STRING, description="type"),
            },
            required=['otp_key']
        ),
        responses={
            201: openapi.Response(description="Otp send"),
            400: openapi.Response(description="Failed to send otp code"),
        }
    )
    def resend_otp(self, request, *args, **kwargs):
        otp_key = request.data.get('otp_key')
        f_type = request.data.get('type')

        if f_type == 'register':
            otp_obj = OTPRegisterResend.objects.filter(otp_key=otp_key, deleted_at=None).first()
            if not otp_obj:
                return Response(data={"error": "Otp key is wrong"}, status=status.HTTP_400_BAD_REQUEST)
            objs = OTPRegisterResend.objects.filter(otp_user=otp_obj.otp_user, deleted_at=None).order_by(
                '-created_at')
            if not checking_number_of_otp(objs):
                return Response(data={"error": "Try again 12 hours later"}, status=status.HTTP_400_BAD_REQUEST)
            if not check_resend_otp_code(otp_obj.created_at):
                return Response(data={"error": "Try again a minute later"}, status=status.HTTP_400_BAD_REQUEST)
            if checking_number_of_otp(objs) == 'delete':
                objs = OTPRegisterResend.objects.filter(otp_user=otp_obj.otp_user, deleted_at=None)
                for obj in objs:
                    obj.deleted_at = datetime.now()
                    obj.save(update_fields=['deleted_at'])
            new_otp = OTPRegisterResend.objects.create(otp_user=otp_obj.otp_user)
            new_otp.save()
            response = send_message_telegram(new_otp)
            if response.status_code != 200:
                new_otp.deleted_at = datetime.now()
                new_otp.save(update_fields=['deleted_at'])
                return Response(data={"error": "Failed to send otp code"}, status=status.HTTP_400_BAD_REQUEST)
            otp_obj.deleted_at = datetime.now()
            otp_obj.save(update_fields=['deleted_at'])
            return Response(data={"otp_key": new_otp.otp_key}, status=status.HTTP_200_OK)
        else:
            otp_obj = OTPSetPassword.objects.filter(otp_key=otp_key, deleted_at=None).first()
            if not otp_obj:
                return Response(data={"error": "Otp key is wrong"}, status=status.HTTP_400_BAD_REQUEST)
            objs = OTPSetPassword.objects.filter(otp_user=otp_obj.otp_user, deleted_at=None).order_by(
                '-created_at')
            if not checking_number_of_otp(objs):
                return Response(data={"error": "Try again 12 hours later"}, status=status.HTTP_400_BAD_REQUEST)
            if not check_resend_otp_code(otp_obj.created_at):
                return Response(data={"error": "Try again a minute later"}, status=status.HTTP_400_BAD_REQUEST)
            if checking_number_of_otp(objs) == 'delete':
                objs = OTPSetPassword.objects.filter(otp_user=otp_obj.otp_user, deleted_at=None)
                for obj in objs:
                    obj.deleted_at = datetime.now()
                    obj.save(update_fields=['deleted_at'])
            new_otp = OTPSetPassword.objects.create(otp_user=otp_obj.otp_user)
            new_otp.save()
            response = send_message_telegram(new_otp)
            if response.status_code != 200:
                new_otp.deleted_at = datetime.now()
                new_otp.save(update_fields=['deleted_at'])
                return Response(data={"error": "Failed to send otp code"}, status=status.HTTP_400_BAD_REQUEST)
            otp_obj.deleted_at = datetime.now()
            otp_obj.save(update_fields=['deleted_at'])
            return Response(data={"otp_key": new_otp.otp_key}, status=status.HTTP_200_OK)