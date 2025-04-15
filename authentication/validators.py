from django.core.exceptions import ValidationError


def validate_uz_phone_number(phone_number: str):
    number_codes = ('99', '98', '97', '95', '94', '93', '91', '90', '77', '55', '33', '71')
    phone_number = phone_number.replace(' ', '')
    if len(phone_number) != 13:
        raise ValidationError("Telefon raqamining uzuznligi 13 bo`lishi kerak!")
    if not phone_number.startswith('+998'):
        raise ValidationError("Telefon raqami +998 bilan boshlanishi kerak!")
    if not phone_number[3:5] in number_codes:
        return ValidationError("Telefon nomer kodi uzbek kodi emas")
    if not phone_number[1:].isdigit():
        raise ValidationError("Telefon raqami faqat butun sonlar(0,1,2,3,4,5,6,7,8,9) iborat bo`lishi kerak!")
