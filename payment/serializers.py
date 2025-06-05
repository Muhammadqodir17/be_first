from rest_framework import serializers
from payment.models import PurchaseModel


class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseModel
        fields = ['id', 'user', 'participant', 'competition', 'price', 'is_active']


class GetPurchaseSerializer(serializers.ModelSerializer):
    phone_number = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseModel
        fields = ['price', 'user', 'phone_number', 'id', 'created_at']

    def get_phone_number(self, obj):
        return obj.user.phone_number

    def get_user(self, obj):
        return f'{obj.user.first_name} {obj.user.last_name}'


