import random
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.conf import settings
from datetime import datetime, timedelta
import requests

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


def send_message_telegram(otp_obj):
    message = {
        'otp_key': otp_obj.otp_key,
        'otp_code': otp_obj.otp_code
    }
    return requests.get(TELEGRAM_API_URL.format(BOT_ID, message, CHAT_ID))


def checking_number_of_otp(checking):
    current_time = datetime.now()
    if len(checking) >= 3:
        obj = checking[0]
        if current_time - obj.created_at < timedelta(hours=12):
            return False
        return 'delete'
    return True


def check_resend_otp_code(created_at):
    current_time = datetime.now()
    if current_time - created_at < timedelta(minutes=1):
        return False
    return True


def check_token_expire(created_at):
    current_time = datetime.now()
    if (current_time - created_at) > timedelta(minutes=30):
        return False
    return True


def check_code_expire(created_at):
    current_time = datetime.now()
    if current_time - created_at > timedelta(minutes=3):
        return False
    return True


def generate_otp_code():
    return random.randint(10000, 99999)

