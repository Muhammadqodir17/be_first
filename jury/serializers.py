from rest_framework import serializers
from konkurs.models import (
    Competition,
    Participant,
    ChildWork
)
from .models import Assessment


class ActiveCompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = ['id', 'name']


class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = ['id', 'child']


class CompetitionSerializer(serializers.ModelSerializer):
    participants = serializers.SerializerMethodField(source='get_participants')
    class Meta:
        model = Competition
        fields = ['id', 'name', 'comp_end_date', 'participants']

    def get_participants(self, obj):
        participants = Participant.objects.filter(competition__id=obj.competition.id)
        if participants:
            return ParticipantSerializer(participants, many=True).data
        return None


class WorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChildWork
        fields = ['id', 'files']


class ParticipantWorkSerializer(serializers.ModelSerializer):
    works = serializers.SerializerMethodField(source='get_works')
    class Meta:
        model = Participant
        fields = ['id', 'works']

    def get_works(self, obj):
        works = ChildWork.objects.filter(participant__id=obj.id, competition__id=obj.competition.id)
        if works:
            return WorkSerializer(works, many=True).data
        return None


class MarkSerializer(serializers.ModelSerializer):
    participant = ParticipantSerializer()
    class Meta:
        model = Assessment
        fields = ['id', 'jury', 'participant', 'grade', 'comment', 'competition']


class AssessmentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = ['id', 'participant', 'competition', 'grade', 'comment']
