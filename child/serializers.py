from rest_framework import serializers
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


class ChildWorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChildWork
        fields = ['id', 'participant', 'competition', 'files']


class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = ['id', 'competition', 'child', 'physical_certificate', 'approve', 'marked_status']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['approve'] = instance.approve
        return data