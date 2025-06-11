import requests
import base64
from datetime import datetime, timedelta
from dataclasses import dataclass
from django.utils.translation import gettext_lazy as _, get_language
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from konkurs.models import Participant
from django.conf import settings

from konkurs_admin.models import Winner
from konkurs_admin.serializers import DownloadCertificateSerializer, PurchaseInfoSerializer
from payment.models import PurchaseModel
from payment.serializers import PurchaseSerializer
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from payment.utils import validate_pan, validate_expiry

s = settings.ATMOS_AUTH
store_id = settings.STORE_ID


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
        participant_id = request.data.get('participant_id')
        participant = Participant.objects.filter(id=participant_id).first()

        if not participant:
            return Response(data={'error': _('Participant not found')}, status=status.HTTP_404_NOT_FOUND)

        if PurchaseModel.objects.filter(user=participant.child.user, participant=participant,
                                        competition=participant.competition, is_active=True).exists():
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
            return Response(data={'error': result.get('description')}, status=status.HTTP_400_BAD_REQUEST)
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
                'card_number': openapi.Schema(type=openapi.TYPE_STRING, description='card_number'),
                'card_expiry': openapi.Schema(type=openapi.TYPE_STRING, description='card_expiry'),
                'transaction_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='transaction_id'),
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
        validate_pan(request.data['card_number'])
        validate_expiry(request.data['card_expiry'])
        expiry = str(request.data['card_expiry'])
        month = expiry[:2]
        year = expiry[3:]
        res_expiry = year + month
        print('=' * 100)
        print(res_expiry)
        print((request.data['card_number']))
        print('=' * 100)
        token = atmos_token()
        response = requests.post(
            'https://partner.atmos.uz/merchant/pay/pre-apply',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            json={
                "card_number": str(request.data['card_number']),
                "expiry": str(res_expiry),
                "store_id": int(store_id),
                "transaction_id": int(request.data['transaction_id']),
                "lang": get_language(),
            }
        )
        data = response.json()
        result = data.get("result", {})
        if response.status_code != 200 or result['code'] != "OK":
            return Response(data={'error': result.get('description')}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data={'transaction_id': int(request.data['transaction_id'])}, status=status.HTTP_200_OK)

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
            return Response(data={'error': result.get('description')}, status=status.HTTP_400_BAD_REQUEST)
        purchase.is_active = True
        purchase.save(update_fields=['is_active'])
        participant.is_paid = True
        participant.save(update_fields=['is_paid'])
        return Response(data={'success': True}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Download Certificate",
        operation_summary="Download Certificate",
        manual_parameters=[
            openapi.Parameter(
                'participant', openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description='participant_id',
                required=True
            )
        ],
        responses={200: DownloadCertificateSerializer()},
        tags=['payment'],
    )
    def download_certificate(self, request, *args, **kwargs):
        data = request.GET
        participant = Participant.objects.filter(id=data.get('participant')).first()

        if participant is None:
            return Response(data={'error': _('Participant not found')}, status=status.HTTP_404_NOT_FOUND)

        if participant.is_paid is False:
            return Response(data={'ok': False}, status=status.HTTP_200_OK)

        winner = Winner.objects.filter(participant=participant).first()
        if winner is None:
            return Response(data={'error': _('Winner not found')}, status=status.HTTP_404_NOT_FOUND)

        serializer = DownloadCertificateSerializer(winner, context={'request': request})

        response = Response(data=serializer.data, content_type='image/*' , status=status.HTTP_200_OK)
        response.headers['Content-Disposition'] = 'attachment'
        response.headers['filename'] = winner.certificate.name
        return response

    # @swagger_auto_schema(
    #     operation_description="Get Payment Info",
    #     operation_summary="Get Payment Info",
    #     responses={
    #         200: PurchaseInfoSerializer(),
    #     },
    #     tags=['payment']
    # )
    # def payment_info(self, request, *args, **kwargs):
    #     purchase = PurchaseModel.objects.filter(participant__id=kwargs['pk']).first()
    #     if purchase is None:
    #         return Response(data={'error': 'Purchase not found'}, status=status.HTTP_404_NOT_FOUND)
    #     serializer = PurchaseInfoSerializer(purchase)
    #     return Response(data=serializer.data, status=status.HTTP_200_OK)