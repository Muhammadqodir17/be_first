from datetime import datetime, timedelta
import requests
from dataclasses import dataclass
from django.utils.translation import gettext_lazy as _, get_language
from os import getenv

from authentication.models import User
from payment.models import CardModel


class PaymentError(Exception):
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code


@dataclass
class Token:
    token: str
    expires: datetime


instance: Token | None = None


def atmos_token():
    global instance
    if instance is None or instance.expires <= datetime.now():
        instance = Token(**get_new_token_data())
    return instance.token


def get_new_token_data() -> dict:
    response = requests.post(
        'https://partner.atmos.uz/token',
        headers={
            'Authorization': f'Basic {getenv("ATMOS_AUTH")}',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'partner.atmos.uz'
        },
        data={'grant_type': 'client_credentials'}
    )
    token_data = response.json()
    if response.status_code == 200:
        return {
            'token': token_data['access_token'],
            'expires': datetime.now() + timedelta(hours=1)
        }
    raise Exception("Failed to obtain new token")


def bind_card_init(number: str, expires: int) -> int:
    token = atmos_token()
    response = requests.post(
        'https://partner.atmos.uz/partner/bind-card/init',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        json={
            "card_number": number,
            "expiry": expires
        }
    )
    data = response.json()
    result = data.get("result", {})
    if response.status_code != 200 or result['code'] != "OK":
        raise PaymentError(result["description"], result["code"])
    return data.get('transaction_id')


def bind_card_confirm(transaction_id: str, otp: str, user_id: int) -> CardModel:
    token = atmos_token()
    response = requests.post(
        "https://partner.atmos.uz/partner/bind-card/confirm",
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        json={
            "transaction_id": transaction_id,
            "otp": otp
        }
    )
    result_data = response.json()
    result = result_data.get("result", {})
    data = result_data.get("data", {})
    if response.status_code != 200 or result['code'] != "OK":
        raise PaymentError(result.get("description"), result['code'])
    card = CardModel(
        card_id=data.get('card_id'),
        token=data.get('card_token'),
        pan=data.get('pan'),
        expires=data.get('expiry'),
        holder=data.get('card_holder'),
        balance=data.get('balance') or 0,
        phone=data.get('phone'),
        user_id=user_id,
    )
    card.save()
    return card


def card_remove(card_id: int, card_token: str) -> bool:
    token = atmos_token()
    response = requests.post(
        "https://partner.atmos.uz/partner/remove-card",
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        json={
            "id": card_id,
            "token": card_token
        }
    )
    data = response.json()
    result = data.get("result", {})
    if response.status_code != 200 or result['code'] != "OK":
        raise PaymentError(result["description"], result["code"])
    return True


def pay_create(amount: int, account: int):
    token = atmos_token()
    response = requests.post(
        "https://partner.atmos.uz/merchant/pay/create",
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        json={
            "amount": amount,
            "store_id": int(getenv("STORE_ID")),
            "account": account,
            "lang": get_language(),
        }
    )
    data = response.json()
    result = data.get("result", {})
    if response.status_code != 200 or result['code'] != "OK":
        raise PaymentError(result["description"], result["code"])
    return data.get('transaction_id')


def pay_pre_apply(transaction_id, card_token: str = None, card_number: str = None, card_expiry: int = None):
    token = atmos_token()
    payload = {
        "store_id": int(getenv("STORE_ID")),
        "transaction_id": transaction_id,
        "lang": get_language()
    }
    if card_number and card_expiry:
        payload.update({"card_number": card_number, "expiry": card_expiry})
    elif card_token:
        payload.update({"card_token": card_token})
    else:
        raise ValueError("card_number or card_expiry is required")

    response = requests.post(
        'https://partner.atmos.uz/merchant/pay/pre-apply',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        json=payload
    )
    data = response.json()
    result = data.get("result", {})
    if response.status_code != 200 or result['code'] != "OK":
        raise PaymentError(result["description"], result["code"])
    return transaction_id


def pay_apply(transaction_id: int, otp: int):
    token = atmos_token()
    payload = {
        "transaction_id": transaction_id,
        "otp": otp,
        "store_id": int(getenv("STORE_ID")),
        "lang": get_language()
    }
    response = requests.post(
        "https://partner.atmos.uz/merchant/pay/apply-ofd",
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        json=payload
    )
    data = response.json()
    result = data.get("result", {})
    if response.status_code != 200 or result['code'] != "OK":
        raise PaymentError(result["description"], result["code"])
    return True


def get_user_card(user: User, card_id: int | None = None):
    if card_id:
        return user.cards.get(id=card_id)
    return user.cards.first()


def get_user_cards(user: User):
    return list(user.cards.all())




##############################################################
from authentication.models import User
from .models import PurchaseModel
from django.utils.translation import gettext as _


def is_singer_available(singer_id: int, user: User=None, user_id: int=None) -> tuple[bool, str | SingerModel]:
    if not (user or user_id):
        raise TypeError("user or user_id are required")
    singers = SingerModel.objects.filter(channel_id=singer_id).active_translations()
    if not singers.exists():
        return False, "Sorry, the singer you entered doesn't exist."
    singer = singers.first()
    if user is None:
        try:
            user = User.objects.prefetch_related('purchases').get(user_id=user_id)
        except User.DoesNotExist:
            return False, "Lets authorize press /start and sign_in"
    purchase = user.purchases.filter(singer=singer, is_active=True)
    return purchase.exists(), singer

def user_by_id(user_id: int) -> tuple[bool, User]:
    users = User.objects.filter(user_id=user_id)
    return users.exists(), users.first()

def user_create(**kwargs) -> User:
    return User.objects.create(**kwargs)

def user_update(user_id: int, **kwargs):
    User.objects.filter(user_id=user_id).update(**kwargs)

def users_all(offset: int, limit: int):
    return list(User.objects.all()[offset:offset + limit]), User.objects.count()

def purchase_create(**kwargs):
    return PurchaseModel.objects.create(**kwargs)

def purchase_accept(purchase: PurchaseModel):
    purchase.is_active = True
    purchase.save()

def delete(obj):
    obj.delete()