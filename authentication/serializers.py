from django.utils.translation import gettext_lazy as _
from numpy.random import random_sample

from .models import User, BlacklistedAccessToken
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy  as _
from .utils import is_valid_tokens
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from .validators import (
    validate_uz_phone_number,
    validate_name,
    validate_password
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['phone_number', 'first_name', 'last_name', 'middle_name', 'birth_date', 'email', 'speciality',
                  'academic_degree', 'place_of_work', 'role']

    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError(_('Incorrect email format'))
        return value


class SetPasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'old_password', 'new_password', 'confirm_password']

    def validate(self, data):
        user = self.context['request'].user
        if not user.check_password(data['old_password']):
            raise serializers.ValidationError({'old_password': _('Old password is incorrect.')})
        validate_password(data['new_password'])
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': _('Passwords do not match.')})
        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)
    access_token = serializers.CharField(required=True)

    def validate(self, data):
        refresh_token = data.get('refresh_token')
        access_token = data.get('access_token')
        if not is_valid_tokens(refresh_token, access_token):
            raise serializers.ValidationError(_('Access token or Refresh token is invalid or expired'))
        refresh_blacklisted = BlacklistedToken.objects.filter(token__token=refresh_token).exists()
        access_blacklisted = BlacklistedAccessToken.objects.filter(token=access_token).exists()

        if refresh_blacklisted or access_blacklisted:
            raise serializers.ValidationError(_('Tokens are already in blacklist'))
        return data


class SetProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'image', 'first_name', 'last_name', 'middle_name', 'email',
                  'birth_date', 'phone_number']

    def validate(self, date):
        if date.get('phone_number'):
            validate_uz_phone_number(date['phone_number'])
        if date.get('first_name'):
            validate_name(date['first_name'])
        if date.get('last_name'):
            validate_name(date['last_name'])
        if date.get('middle_name'):
            validate_name(date['middle_name'])
        return date


class RegisterSerializers(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'middle_name', 'birth_date', 'email', 'phone_number',
                  'password', 'confirm_password']

    def validate_first_name(self, value):
        return validate_name(value)

    def validate_last_name(self, value):
        return validate_name(value)

    def validate_middle_name(self, value):
        return validate_name(value)

    def validate_phone_number(self, value):
        return validate_uz_phone_number(value)

    def validate_password(self, value):
        return validate_password(value)

    def validate(self, data):
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({
                'confirm_password': _('Password confirmation does not match.')
            })
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)


class TestSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['id', 'password', 'confirm_password']

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': _('Confirm password does not match.')})
        return data

    def save(self, **kwargs):
        self.instance.password = make_password(self.validated_data['password'])
        self.instance.save(update_fields=['password'])
        return self.instance
