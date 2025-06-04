from rest_framework import serializers
from payment.models import PurchaseModel


class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseModel
        fields = ['id', 'user', 'participant', 'competition', 'price', 'is_active']


class GetPurchaseSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField()
    class Meta:
        model = PurchaseModel
        fields = ['price', 'user', 'phone_number', 'id', 'created_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user'] = f'{instance.user.first_name} {instance.user.last_name}'
        data['phone_number'] = instance.user.phone_number
        return data


