from datetime import date
from rest_framework import serializers
from authentication.models import User
from child.models import Child
from jury.models import Assessment
from konkurs_admin.models import (
    Notification,
    Winner,
    ResultImage,
    WebCertificate, SubscriptionModel
)
from .models import (
    Competition,
    STATUS,
    APPROVEMENT,
    MARKED_STATUS,
    Participant,
    ChildWork
)
from django.conf import settings
from konkurs.models import ContactUs
from django.utils.translation import gettext_lazy as _


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = ['id', 'image', 'name', 'description']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        lang = request.headers.get('Accept-Language', settings.MODELTRANSLATION_DEFAULT_LANGUAGE)
        lang_options = settings.MODELTRANSLATION_LANGUAGES
        if lang in lang_options:
            data['name'] = getattr(instance, f'name_{lang}')
            data['description'] = getattr(instance, f'description_{lang}')
        return data


class CompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = ['id', 'name', 'category', 'prize', 'description', 'application_start_date',
                  'application_start_time', 'application_end_date', 'application_end_time',
                  'rules', 'physical_certificate', 'image', 'status']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['status'] = dict(STATUS).get(instance.status, 'Unknown')
        return data


class GetCompSerializer(serializers.ModelSerializer):
    participants = serializers.SerializerMethodField(source='get_participants')

    class Meta:
        model = Competition
        fields = ['id', 'name', 'category', 'description', 'prize', 'comp_start_date', 'comp_start_time',
                  'comp_end_date', 'comp_end_time', 'application_start_date', 'application_start_time',
                  'application_end_date', 'application_end_time', 'participation_fee', 'rules', 'physical_certificate',
                  'image', 'status', 'participants']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        lang = request.headers.get('Accept-Language', settings.MODELTRANSLATION_DEFAULT_LANGUAGE)
        lang_options = settings.MODELTRANSLATION_LANGUAGES
        if lang in lang_options:
            data['name'] = getattr(instance, f'name_{lang}')
            data['description'] = getattr(instance, f'description_{lang}')
        return data

    def get_participants(self, obj):
        return Participant.objects.filter(competition=obj).count()


class CompAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = ['id', 'grade', 'comment']


class HomeCompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = ['id', 'image', 'name', 'description', 'rules', 'application_end_date', ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        lang = request.headers.get('Accept-Language', settings.MODELTRANSLATION_DEFAULT_LANGUAGE)
        lang_options = settings.MODELTRANSLATION_LANGUAGES
        if lang in lang_options:
            data['name'] = getattr(instance, f'name_{lang}')
            data['description'] = getattr(instance, f'description_{lang}')
        return data


class CompetitionForCompetitionPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = ['id', 'name', 'description', 'image']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        lang = request.headers.get('Accept-Language', settings.MODELTRANSLATION_DEFAULT_LANGUAGE)
        lang_options = settings.MODELTRANSLATION_LANGUAGES
        if lang in lang_options:
            data['name'] = getattr(instance, f'name_{lang}')
            data['description'] = getattr(instance, f'description_{lang}')
        return data


class PersonalInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'birth_date', 'email', 'phone_number', 'image', 'role']


class ChildrenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Child
        fields = ['id', 'user', 'first_name', 'last_name', 'middle_name',
                  'date_of_birth', 'place_of_study', 'degree_of_kinship']


class WorksSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChildWork
        fields = ['id', 'files']


class GetRegisteredChild(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(source='get_name')
    works = serializers.SerializerMethodField(source='get_works')

    class Meta:
        model = Participant
        fields = ['id', 'name', 'works']

    def get_name(self, data):
        return data.child.first_name

    def get_works(self, data):
        request = self.context.get('request')
        works = ChildWork.objects.filter(participant__id=data.id)
        return WorksSerializer(works, many=True, context={'request': request})


class ChildSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()

    class Meta:
        model = Child
        fields = ['id', 'first_name', 'last_name', 'middle_name', 'date_of_birth', 'age', 'place_of_study']

    def get_age(self, obj):
        today = date.today()
        birthdate = obj.date_of_birth
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

        return age


class ParticipantSerializer(serializers.ModelSerializer):
    competition = CompetitionSerializer()
    child = ChildSerializer()

    class Meta:
        model = Participant
        fields = ['id', 'child', 'action', 'competition', 'physical_certificate', 'marked_status']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['action'] = dict(APPROVEMENT).get(instance.action, 'Unknown')
        data['marked_status'] = dict(MARKED_STATUS).get(instance.marked_status, 'Unknown')
        return data


class CompSerializer(serializers.ModelSerializer):
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


class CompParticipantSerializer(serializers.ModelSerializer):
    competition = CompSerializer()

    class Meta:
        model = Participant
        fields = ['id', 'child', 'competition']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['child'] = f'{instance.child.first_name} {instance.child.last_name}'
        return data


class ActiveCompSerializer(serializers.ModelSerializer):
    participants = serializers.SerializerMethodField()

    class Meta:
        model = Competition
        fields = ['id', 'name', 'participants', 'comp_end_date', 'description']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        lang = request.headers.get('Accept-Language', settings.MODELTRANSLATION_DEFAULT_LANGUAGE)
        lang_options = settings.MODELTRANSLATION_LANGUAGES
        if lang in lang_options:
            data['name'] = getattr(instance, f'name_{lang}')
            data['description'] = getattr(instance, f'description_{lang}')
        return data

    def get_participants(self, obj):
        participants = Participant.objects.filter(competition__id=obj.id).count()
        return participants


class ActiveParticipantSerializer(serializers.ModelSerializer):
    competition = ActiveCompSerializer()

    class Meta:
        model = Participant
        fields = ['child', 'competition']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['child'] = f'{instance.child.first_name} {instance.child.last_name}'
        return data


class FinishedCompSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = ['id', 'name', 'description']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        lang = request.headers.get('Accept-Language', settings.MODELTRANSLATION_DEFAULT_LANGUAGE)
        lang_options = settings.MODELTRANSLATION_LANGUAGES
        if lang in lang_options:
            data['name'] = getattr(instance, f'name_{lang}')
            data['description'] = getattr(instance, f'description_{lang}')
        return data


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = ['id', 'grade', 'comment']


class FinishedParticipantSerializer(serializers.ModelSerializer):
    competition = FinishedCompSerializer()
    grade = serializers.CharField(read_only=True)
    certificate = serializers.CharField(read_only=True)

    class Meta:
        model = Participant
        fields = ['child', 'competition', 'grade', 'certificate']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['child'] = f'{instance.child.first_name} {instance.child.last_name}'
        request = self.context.get('request')
        grade_instance = Assessment.objects.filter(
            participant=instance, competition=instance.competition
        ).first()
        data['grade'] = GradeSerializer(grade_instance).data if grade_instance else None

        winner = Winner.objects.filter(
            participant=instance, competition=instance.competition
        ).first()
        if winner and winner.certificate:
            data['certificate'] = True
        else:
            data['certificate'] = None

        return data


class WorksSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChildWork
        fields = ['id', 'competition', 'files']


class GallerySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChildWork
        fields = ['competition', 'files']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        lang = request.headers.get('Accept-Language', settings.MODELTRANSLATION_DEFAULT_LANGUAGE)
        lang_options = settings.MODELTRANSLATION_LANGUAGES
        if instance.competition is not None:
            if lang in lang_options:
                data['competition'] = getattr(instance.competition, f'name_{lang}')
            else:
                data['competition'] = instance.competition.name
        else:
            data['competition'] = None
        return data


class CompGallerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = ['name', 'category']


class GalleryDetailsSerializer(serializers.ModelSerializer):
    competition = CompGallerySerializer()
    files = serializers.SerializerMethodField(source='get_files')

    class Meta:
        model = Participant
        fields = ['competition', 'child', 'files']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        lang = request.headers.get('Accept-Language', settings.MODELTRANSLATION_DEFAULT_LANGUAGE)
        lang_options = settings.MODELTRANSLATION_LANGUAGES
        if lang in lang_options:
            data['competition'] = getattr(instance.competition, f'name_{lang}')
        return data

    def get_files(self, obj):
        file_instance = ChildWork.objects.filter(participant__id=obj.id).first()
        if file_instance:
            return WorksSerializer(file_instance).data
        return None


class ExpertSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'speciality', 'place_of_work', 'image']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        lang = request.headers.get('Accept-Language', settings.MODELTRANSLATION_DEFAULT_LANGUAGE)
        lang_options = settings.MODELTRANSLATION_LANGUAGES
        if lang in lang_options:
            data['speciality'] = getattr(instance, f'speciality_{lang}')
            data['place_of_work'] = getattr(instance, f'place_of_work_{lang}')
        data['speciality'] = instance.speciality
        data['place_of_work'] = instance.place_of_work
        return data


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'child', 'competition', 'grade', 'comment', 'message', 'is_read']


class ResultImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultImage
        fields = ['id', 'name', 'image']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['name'] = instance.get_name_display()
        return data


class WebCerSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebCertificate
        fields = ['image']


class ResultsSerializer(serializers.Serializer):
    pass


class ContactUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactUs
        fields = ['id', 'email', 'replied']


class GetSubscriptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionModel
        fields = ['id', 'competition']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['competition_id'] = instance.competition.id
        data['competition'] = instance.competition.name
        return data


class SubscribeCompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionModel
        fields = ['id', 'user', 'competition']
