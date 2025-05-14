import re
import requests
from django.utils.translation import gettext_lazy as _
from random import randint
from django.utils.timezone import now
from datetime import datetime, timedelta
from .models import User, SMSCode, TemporaryPassword, BlacklistedAccessToken
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from .utils import is_valid_tokens
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from .validators import validate_uz_phone_number

BOT_TOKEN = '7662698791:AAFF7tOLoXxRhLIwL5ltuEuxpsyqIm4UUKE'
CHAT_ID = '5467422443'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['phone_number', 'first_name', 'last_name', 'middle_name', 'birth_date', 'email', 'speciality',
                  'academic_degree', 'place_of_work', 'role']

    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError(_('Inccorrect email format'))
        return value


class SendSMSSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

    def validate_phone_number(self, value):
        if not re.match(r'^\+998\d{9}$', value):
            raise serializers.ValidationError(_("Phone number must be in the format +998XXXXXXXXX."))
        return value


class VerifySMSSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    code = serializers.CharField()

    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        code = attrs.get('code')

        if not phone_number or not code:
            raise serializers.ValidationError(_("Phone number and code fields are required."))

        try:
            sms_code = SMSCode.objects.get(phone_number=phone_number, code=code)
        except SMSCode.DoesNotExist:
            raise serializers.ValidationError(_("Incorrect code."))

        if sms_code.expires_at < datetime.now():
            raise serializers.ValidationError(_("Code expired."))

        attrs['sms_code'] = sms_code
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Old password is not correct."))
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": _("Passwords do not match.")})
        return data

    def validate_password(self, value):
        if len(value) < 8 or not any(char.isdigit() for char in value) or not any(char.isupper() for char in value):
            raise serializers.ValidationError(
                _("The password must contain a minimum of 8 characters, one capital letter, and one number.")
            )
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        password = attrs.get('password')

        if not phone_number or not password:
            raise serializers.ValidationError(_("Phone number and password are required."))

        user = authenticate(username=phone_number, password=password)
        if user is None:
            raise serializers.ValidationError(_("Invalid phone number or password."))

        attrs['user'] = user
        return attrs


class SendTempPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

    def validate_phone_number(self, value):
        if not value.startswith("+") or not value[1:].isdigit():
            raise serializers.ValidationError(_("Invalid phone number format."))
        return value

    def create(self, validated_data):
        phone_number = validated_data['phone_number']
        temp_password = str(randint(100000, 999999))
        temp_password_entry, created = TemporaryPassword.objects.update_or_create(
            phone_number=phone_number,
            defaults={'temp_password': temp_password, 'created_at': now()}
        )

        message = _("Your verification code to reset your password is: %(temp_password)s") % {'code': temp_password}
        telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
        response = requests.get(telegram_url)

        if response.status_code != 200:
            raise serializers.ValidationError(_("Failed to send message."))

        return temp_password_entry


class SetPasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(_("The password must contain a minimum of 8 characters."))
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError(_("The password must contain at least one uppercase letter."))
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError(_("The password must contain at least one number."))
        return value

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Old password is not correct."))
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": _("Passwords do not match.")})
        return data

    def validate_password(self, value):
        if len(value) < 8 or not any(char.isdigit() for char in value) or not any(char.isupper() for char in value):
            raise serializers.ValidationError(
                _("The password must contain a minimum of 8 characters, one capital letter, and one number.")
            )
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)
    access_token = serializers.CharField(required=True)

    def validate(self, data):
        refresh_token = data.get('refresh_token')
        access_token = data.get('access_token')
        if not is_valid_tokens(refresh_token, access_token):
            raise serializers.ValidationError('Access token or Refresh token is invalid or expired')
        refresh_blacklisted = BlacklistedToken.objects.filter(token__token=refresh_token).exists()
        access_blacklisted = BlacklistedAccessToken.objects.filter(token=access_token).exists()

        if refresh_blacklisted or access_blacklisted:
            raise serializers.ValidationError('Tokens are already in blacklist', code=400)
        return data


class SetProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'image', 'first_name', 'last_name', 'middle_name', 'email',
                  'birth_date', 'phone_number']

    def validate(self, attrs):
        phone_number = attrs['phone_number']
        validate_uz_phone_number(phone_number)
        return attrs


class RegisterSerializers(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'middle_name', 'birth_date', 'email', 'phone_number',
                  'password', 'confirm_password']

    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Enter a valid email address.")
        return value

    def validate_phone_number(self, value):
        try:
            validate_uz_phone_number(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate_confirm_password(self, value):
        request_data = self.initial_data
        if 'password' in request_data and value != request_data['password']:
            raise serializers.ValidationError("Passwords do not match.")
        return value

    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)


class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(_("The password must contain a minimum of 8 characters."))
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError(_("The password must contain at least one uppercase letter."))
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError(_("The password must contain at least one number."))
        return value

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Old password is not correct."))
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": _("Passwords do not match.")})
        return data

    def validate_password(self, value):
        if len(value) < 8 or not any(char.isdigit() for char in value) or not any(char.isupper() for char in value):
            raise serializers.ValidationError(
                _("The password must contain a minimum of 8 characters, one capital letter, and one number.")
            )
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class ReSetPassSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'new_password', 'confirm_password']

    def validate(self, attrs):
        # phone_number = attrs['phone_number']
        # validate_uz_phone_number(phone_number)
        print(attrs)
        return attrs


    # def phone_validate(self, data):
    #     validate_uz_phone_number(data['phone_number'])
    #
    # def validate_new_password(self, value):
    #     if len(value) < 8:
    #         raise serializers.ValidationError(_("The password must contain a minimum of 8 characters."))
    #     if not any(char.isupper() for char in value):
    #         raise serializers.ValidationError(_("The password must contain at least one uppercase letter."))
    #     if not any(char.isdigit() for char in value):
    #         raise serializers.ValidationError(_("The password must contain at least one number."))
    #     return value
    #
    # def validate(self, data):
    #     if data['new_password'] != data['confirm_password']:
    #         raise serializers.ValidationError({"confirm_password": _("Passwords do not match.")})
    #     return data
    #
    # def validate_password(self, value):
    #     if len(value) < 8 or not any(char.isdigit() for char in value) or not any(char.isupper() for char in value):
    #         raise serializers.ValidationError(
    #             _("The password must contain a minimum of 8 characters, one capital letter, and one number.")
    #         )
    #     return value

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     print(data)
    #     print(instance)
    #     data['password'] = data['new_password']
    #     return data


