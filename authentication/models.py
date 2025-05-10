from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import UserManager
from django.utils.timezone import now
from datetime import timedelta
from base.model import BaseModel

ROLE_CHOICES = (
    (0, '---'),
    (1, 'Candidate'),
    (2, 'Jury'),
    (3, 'Admin'),
)

ACADEMIC_DEGREE = (
    (0, '---'),
    (1, 'Associate'),
    (2, 'Bachelor'),
    (3, 'Master'),
    (4, 'Doctoral'),
)


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=100, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)

    speciality = models.CharField(max_length=300, blank=True)
    academic_degree = models.IntegerField(choices=ACADEMIC_DEGREE, default=0)
    place_of_work = models.CharField(max_length=300, blank=True)
    category = models.ForeignKey('konkurs.Category', on_delete=models.CASCADE, null=True, blank=True)
    role = models.IntegerField(choices=ROLE_CHOICES, default=0)
    children_count = models.PositiveIntegerField(default=0)

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
