import requests
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.conf import settings
from django.utils.translation import gettext as _

BOT_ID = settings.BOT_ID
CHAT_ID = settings.CHAT_ID
TELEGRAM_API_URL = settings.TELEGRAM_API_URL


def is_valid_tokens(refresh_token, access_token):
    try:
        RefreshToken(refresh_token)
        AccessToken(access_token)
        return True
    except TokenError:
        return False


def send_message_telegram(phone_number, otp_code):
    message = _("Telefon raqami: %(phone)s\nOTP kodi: %(otp)s") % {
        'phone': phone_number,
        'otp': otp_code
    }
    return requests.get(TELEGRAM_API_URL.format(BOT_ID, message, CHAT_ID))
