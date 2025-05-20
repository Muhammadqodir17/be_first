import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import UserManager
from django.utils.timezone import now
from datetime import timedelta
from base.model import BaseModel
from .utils import generate_otp_code
from .validators import validate_uz_phone_number_for_model, validate_name_for_model

ROLE_CHOICES = (
    (0, '---'),
    (1, 'Candidate'),
    (2, 'Jury'),
    (3, 'Admin'),
)

TYPE = (
    (0, '---'),
    (1, 'forgot'),
    (2, 'register'),
)

ACADEMIC_DEGREE = (
    (0, '---'),
    (1, 'Associate'),
    (2, 'Bachelor'),
    (3, 'Master'),
    (4, 'Doctoral'),
)


OTPTYPES = (
    (0, '---'),
    (1, "register"),
    (2, 'resend')
)


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=100, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True, validators=[validate_uz_phone_number_for_model])
    first_name = models.CharField(max_length=50, blank=True, null=True, validators=[validate_name_for_model])
    last_name = models.CharField(max_length=50, blank=True, null=True, validators=[validate_name_for_model])
    middle_name = models.CharField(max_length=50, blank=True, null=True, validators=[validate_name_for_model])
    birth_date = models.DateField(blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)

    speciality = models.CharField(max_length=300, blank=True)
    academic_degree = models.IntegerField(choices=ACADEMIC_DEGREE, default=0)
    place_of_work = models.CharField(max_length=300, blank=True)
    category = models.ForeignKey('konkurs.Category', on_delete=models.CASCADE, null=True, blank=True)
    role = models.IntegerField(choices=ROLE_CHOICES, default=0)
    children_count = models.PositiveIntegerField(default=0)

    is_verified = models.BooleanField(default=False)
    type = models.IntegerField(choices=TYPE, default=0)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    image = models.ImageField(upload_to='media/', null=True)

    USERNAME_FIELD = 'phone_number'

    objects = UserManager()

    def __str__(self):
        if self.username:
            return f'{self.username}'
        return f'{self.phone_number}'



class SMSCode(BaseModel):
    phone_number = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    verified = models.BooleanField(default=False)

    def __str__(self):
        return self.code


class TemporaryPassword(BaseModel):
    phone_number = models.CharField(max_length=15, unique=True)
    temp_password = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        expiration_time = self.created_at + timedelta(minutes=5)
        return now() > expiration_time


class BlacklistedAccessToken(models.Model):
    token = models.CharField(max_length=500, unique=True)
    blacklisted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.blacklisted_at}'


class OTPRegisterResend(models.Model):
    otp_key = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    otp_code = models.PositiveIntegerField(default=generate_otp_code)
    otp_user = models.ForeignKey(User, models.SET_NULL, null=True)
    otp_type = models.IntegerField(choices=OTPTYPES, default=1)
    attempts = models.IntegerField(default=0)

    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.created_at}'


class OTPSetPassword(models.Model):
    otp_key = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    otp_code = models.PositiveIntegerField(default=generate_otp_code)
    otp_token = models.UUIDField(default=uuid.uuid4)
    otp_user = models.ForeignKey(User, models.SET_NULL, null=True)
    attempts = models.IntegerField(default=0)

    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.created_at}'
