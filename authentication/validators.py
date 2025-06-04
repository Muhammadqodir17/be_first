from django.core.exceptions import ValidationError
import re
from rest_framework import serializers
from django.utils.translation import gettext_lazy  as _

def validate_uz_phone_number(phone_number: str):
    # number_codes = ('99', '98', '97', '95', '94', '93', '91', '90', '77', '55', '33', '71')
    phone_number = phone_number.replace(' ', '')
    if not phone_number[1:].isdigit():
        raise serializers.ValidationError(_("Telefon raqami faqat butun sonlar(0,1,2,3,4,5,6,7,8,9) iborat bo`lishi kerak!"))
    if len(phone_number) != 13:
        raise serializers.ValidationError(_("Telefon raqamining uzunligi 13 bo`lishi kerak!"))
    if not phone_number.startswith('+998'):
        raise serializers.ValidationError(_("Telefon raqami +998 bilan boshlanishi kerak!"))
    # if not phone_number[4:6] in number_codes:
    #     return serializers.ValidationError(_("Telefon nomer kodi uzbek kodi emas"))
    return phone_number

def validate_uz_phone_number_for_model(phone_number: str):
    # number_codes = ('99', '98', '97', '95', '94', '93', '91', '90', '77', '55', '33', '71')
    phone_number = phone_number.replace(' ', '')
    if not phone_number[1:].isdigit():
        raise ValidationError(
            _("Telefon raqami faqat butun sonlar(0,1,2,3,4,5,6,7,8,9) iborat bo`lishi kerak!"))
    if len(phone_number) != 13:
        raise ValidationError(_("Telefon raqamining uzunligi 13 bo`lishi kerak!"))
    if not phone_number.startswith('+998'):
        raise ValidationError(_("Telefon raqami +998 bilan boshlanishi kerak!"))
    # if not phone_number[4:6] in number_codes:
    #     return ValidationError(_("Telefon nomer kodi uzbek kodi emas"))
    return phone_number

def validate_name(value: str):
    if not re.fullmatch(r"[A-Za-zА-Яа-яЁёЎўҚқҒғҲҳЪъІіʼ'` ]+", value):
        raise serializers.ValidationError(_("This field must contain only letters."))
    return value

def validate_name_for_model(value: str):
    if not re.fullmatch(r"[A-Za-zА-Яа-яЁёЎўҚқҒғҲҳЪъІіʼ'` ]+", value):
        raise ValidationError(_("This field must contain only letters."))
    return value

def validate_password(password: str):
    if len(password) < 8:
        raise serializers.ValidationError(_("The password must contain a minimum of 8 characters."))
    if not any(char.isupper() for char in password):
        raise serializers.ValidationError(_("The password must contain at least one uppercase letter."))
    if not any(char.isdigit() for char in password):
        raise serializers.ValidationError(_("The password must contain at least one number."))
    if not any(char.isalpha() for char in password):
        raise serializers.ValidationError(_("The password must contain at least one letter."))
    return password
