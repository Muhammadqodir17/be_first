from rest_framework.response import Response
from rest_framework import status

def validate_pan(pan):
    card_number = str(pan).replace(' ', '')
    if not card_number.isdigit():
        return Response(data={'error': 'Card number must contain only digits'}, status=status.HTTP_400_BAD_REQUEST)
    if len(card_number) != 16:
        return Response(data={'error': 'Card number length must be 16'}, status=status.HTTP_400_BAD_REQUEST)
    return pan

def validate_expiry(expiry):
    expiry_data = str(expiry).replace('/', '')
    if not expiry_data.isdigit():
        return Response(data={'error': 'Expiry must contain only digits'}, status=status.HTTP_400_BAD_REQUEST)
    if len(expiry) < 5:
        return Response(data={'error': 'Expiry length must be 5'}, status=status.HTTP_400_BAD_REQUEST)
    return expiry