from rest_framework import serializers

from authentication.validators import validate_name
from .models import Child
from konkurs.models import (
    Participant,
    ChildWork
)


class ChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Child
        fields = ['id', 'user', 'first_name', 'last_name', 'middle_name',
                  'date_of_birth', 'place_of_study', 'degree_of_kinship']

    def validate_first_name(self, attrs):
        return validate_name(attrs)

    def validate_last_name(self, attrs):
        return validate_name(attrs)

    def validate_middle_name(self, attrs):
        return validate_name(attrs)


class ChildWorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChildWork
        fields = ['id', 'participant', 'competition', 'files']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['participant'] = instance.participant.child.first_name
        data['competition'] = instance.participant.competition.id
        return data
