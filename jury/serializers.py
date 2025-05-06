from rest_framework import serializers
from konkurs.models import (
    Competition,
    Participant,
    ChildWork
)
from .models import Assessment
from django.conf import settings


class ActiveCompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = ['id', 'name']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        lang = request.headers.get('Accept-Language', settings.MODELTRANSLATION_DEFAULT_LANGUAGE)
        lang_options = settings.MODELTRANSLATION_LANGUAGES
        if lang in lang_options:
            data['name'] = getattr(instance, f'name_{lang}')
        return data


class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = ['id', 'child']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['child'] = instance.child.first_name
        return data


class CompetitionSerializer(serializers.ModelSerializer):
    participants = serializers.SerializerMethodField(source='get_participants')
    participants_number = serializers.SerializerMethodField(source='get_participants_number')
    class Meta:
        model = Competition
        fields = ['id', 'name', 'participants_number', 'comp_end_date', 'participants']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        lang = request.headers.get('Accept-Language', settings.MODELTRANSLATION_DEFAULT_LANGUAGE)
        lang_options = settings.MODELTRANSLATION_LANGUAGES
        if lang in lang_options:
            data['name'] = getattr(instance, f'name_{lang}')
        return data

    def get_participants(self, obj):
        participants = Participant.objects.filter(competition__id=obj.id)
        if participants:
            return ParticipantSerializer(participants, many=True).data
        return None

    def get_participants_number(self, obj):
        return Participant.objects.filter(competition__id=obj.id).count()


class WorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChildWork
        fields = ['id', 'files']


class ParticipantWorkSerializer(serializers.ModelSerializer):
    works = serializers.SerializerMethodField(source='get_works')
    class Meta:
        model = Participant
        fields = ['id', 'child', 'works']

    def get_works(self, obj):
        works = ChildWork.objects.filter(participant__id=obj.id, competition__id=obj.competition.id)
        if works:
            return WorkSerializer(works, many=True).data
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['child'] = instance.child.first_name
        return data

class MarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = ['id', 'jury', 'participant', 'grade', 'comment', 'competition']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['competition'] = instance.participant.competition.id
        return data


class AssessmentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = ['id', 'participant', 'grade', 'comment']


