import requests
import base64
from datetime import datetime, timedelta
from dataclasses import dataclass
from django.utils.translation import gettext_lazy as _, get_language
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from konkurs.models import Participant
from config.settings import ATMOS_AUTH, STORE_ID
from payment.models import PurchaseModel
from payment.serializers import PurchaseSerializer
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

s = ATMOS_AUTH
store_id = STORE_ID


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
    tokenn = (base64.b64encode(s.encode()).decode())
    response = requests.post(
        'https://partner.atmos.uz/token',
        headers={
            'Authorization': f'Basic {tokenn}',
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
    raise Exception("Failed to obtain new token", response.text)


class PaymentViewSet(ViewSet):
    @swagger_auto_schema(
        operation_description="Create Pay",
        operation_summary="Create Pay",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'participant_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='participant_id'),
                # 'amount': openapi.Schema(type=openapi.TYPE_NUMBER, format='float', description='amount'),
            },
            required=['participant_id']
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'transaction_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='transaction_id'),
                }
            ),
        },
        tags=['payment'],
    )
    def pay_create(self, request, *args, **kwargs):
        user = request.user
        participant_id = request.data.get('participant_id')
        participant = Participant.objects.filter(id=participant_id).first()

        if not participant:
            return Response(data={'error': _('Participant not found')}, status=status.HTTP_404_NOT_FOUND)

        if PurchaseModel.objects.filter(user=user, participant=participant,
                                        competition=participant.competition).exists():
            return Response(data={'error': 'Already purchased'}, status=status.HTTP_400_BAD_REQUEST)

        token = atmos_token()
        participant_id = request.data['participant_id']
        participant = Participant.objects.filter(id=participant_id).first()

        if participant is None:
            return Response(data={'error': _('Participant not found')}, status=status.HTTP_404_NOT_FOUND)

        response = requests.post(
            "https://partner.atmos.uz/merchant/pay/create",
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            json={
                "amount": round(participant.competition.participation_fee * 100),
                "store_id": int(store_id),
                "account": participant.child.user.id,
                "lang": get_language(),
            }
        )
        data = response.json()
        result = data.get("result", {})

        if response.status_code != 200 or result['code'] != "OK":
            raise PaymentError(result["description"], result["code"])
        #
        for_serializer_data = {
            'user': participant.child.user.id,
            'participant': participant.id,
            'competition': participant.competition.id,
            'price': participant.competition.participation_fee,
        }

        serializer = PurchaseSerializer(data=for_serializer_data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()

        return Response(
            data={'transaction_id': data.get('transaction_id'), 'amount': participant.competition.participation_fee},
            status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Pay Pre Apply",
        operation_summary="Pay Pre Apply",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'card_number': openapi.Schema(type=openapi.TYPE_INTEGER, description='name'),
                'card_expiry': openapi.Schema(type=openapi.TYPE_INTEGER, description='name_uz'),
                'transaction_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='name_ru'),
            },
            required=['card_number', 'card_expiry', 'transaction_id']
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'transaction_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='transaction_id'),
                }
            ),
        },
        tags=['payment'],
    )
    def pay_pre_apply(self, request, *args, **kwargs):
        token = atmos_token()
        response = requests.post(
            'https://partner.atmos.uz/merchant/pay/pre-apply',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            json={
                "card_number": str(request.data['card_number']),
                "expiry": str(request.data['card_expiry']),
                "store_id": int(store_id),
                "transaction_id": int(request.data['transaction_id']),
                "lang": get_language(),
            }
        )
        data = response.json()
        result = data.get("result", {})
        if response.status_code != 200 or result['code'] != "OK":
            raise PaymentError(result["description"], result["code"])
        return Response(data={'transaction_id': request.data['transaction_id']}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Pay Apply",
        operation_summary="Pay Apply",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'participant_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='participant_id'),
                'transaction_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='transaction_id'),
                'otp': openapi.Schema(type=openapi.TYPE_INTEGER, description='otp'),
            },
            required=['transaction_id', 'otp', 'participant_id']
        ),
        responses={200: 'True'},
        tags=['payment'],
    )
    def pay_apply(self, request, *args, **kwargs):
        participant_id = request.data.get('participant_id')
        participant = Participant.objects.filter(id=participant_id).first()

        if participant is None:
            return Response(data={'error': _('Participant not found')}, status=status.HTTP_404_NOT_FOUND)

        purchase = PurchaseModel.objects.filter(user=participant.child.user, participant=participant,
                                                competition=participant.competition).first()
        if purchase is None:
            return Response(data={'error': _('Purchase not found')}, status=status.HTTP_400_BAD_REQUEST)

        token = atmos_token()
        payload = {
            "transaction_id": request.data['transaction_id'],
            "otp": request.data['otp'],
            "store_id": int(store_id),
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
        purchase.is_active = True
        purchase.save(update_fields=['is_active'])
        return Response(data={'success': True}, status=status.HTTP_200_OK)
