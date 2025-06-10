from datetime import date
from django.conf import settings
from rest_framework import serializers
from authentication.validators import (
    validate_uz_phone_number,
    validate_name,
    validate_password
)
from jury.models import Assessment
from konkurs.models import (
    Category,
    Competition,
    Participant,
    APPROVEMENT,
    STATUS,
    GradeCriteria,
    ChildWork
)
from child.models import Child
from authentication.models import (
    User,
    ROLE_CHOICES,
    ACADEMIC_DEGREE
)
from django.contrib.auth.hashers import make_password

from payment.models import PurchaseModel
from .models import (
    Winner,
    PLACE,
    ContactInformation,
    AboutResult,
    AboutUs,
    Policy,
    SocialMedia,
)
from django.utils.translation import gettext_lazy as _


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'name_uz', 'name_ru', 'name_en']


class GetCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        lang = request.headers.get('Accept-Language', settings.MODELTRANSLATION_DEFAULT_LANGUAGE)
        lang_options = settings.MODELTRANSLATION_LANGUAGES
        if lang in lang_options:
            data['name'] = getattr(instance, f'name_{lang}')
        return data


class GetCompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = ['id', 'name', 'category', 'description', 'application_start_date', 'application_start_time',
                  'application_end_date', 'application_end_time', 'status']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        lang = request.headers.get('Accept-Language', settings.MODELTRANSLATION_DEFAULT_LANGUAGE)
        lang_options = settings.MODELTRANSLATION_LANGUAGES
        data['status'] = dict(STATUS).get(instance.status, 'Unknown')
        data['category'] = instance.category.name
        if lang in lang_options:
            data['name'] = getattr(instance, f'name_{lang}')
            data['category'] = getattr(instance.category, f'name_{lang}')
            data['description'] = getattr(instance, f'description_{lang}')
        return data


class GetCompetitionByIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = ['id', 'image', 'name', 'category', 'description', 'comp_start_date', 'comp_start_time',
                  'comp_end_date', 'comp_end_time', 'application_start_date', 'application_start_time',
                  'application_end_date', 'application_end_time', 'rules', 'status', 'prize', 'participation_fee',
                  'physical_certificate']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['category'] = instance.category.name
        data['status'] = dict(STATUS).get(instance.status, 'Unknown')
        return data


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
    # child = ChildSerializer()
    full_name = serializers.SerializerMethodField(source='get_full_name')
    date_of_birth = serializers.SerializerMethodField(source='get_date_of_birth')
    age = serializers.SerializerMethodField(source='get_age')
    study_place = serializers.SerializerMethodField(source='get_study_place')

    # works = serializers.SerializerMethodField(source='get_works')

    class Meta:
        model = Participant
        fields = ['id', 'full_name', 'date_of_birth', 'age', 'study_place', 'action']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['action'] = dict(APPROVEMENT).get(instance.action, 'Unknown')
        return data

    def get_works(self, obj):
        works_instance = ChildWork.objects.filter(participant=obj, competition__id=obj.competition.id)
        if works_instance:
            return ChildWorkSerializer(works_instance, many=True).data
        return None

    def get_full_name(self, obj):
        return f'{obj.child.first_name} {obj.child.last_name} {obj.child.middle_name}'

    def get_study_place(self, obj):
        return obj.child.place_of_study

    def get_date_of_birth(self, obj):
        return obj.child.date_of_birth

    def get_age(self, obj):
        today = date.today()
        birthdate = obj.child.date_of_birth
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        return age


# for create
class JurySerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'middle_name', 'phone_number', 'birth_date',
                  'place_of_work', 'place_of_work_uz', 'place_of_work_ru', 'place_of_work_en', 'academic_degree',
                  'speciality', 'speciality_uz', 'speciality_ru', 'speciality_en', 'category',
                  'username', 'password',
                  'confirm_password', 'role', 'image']

    def validate_first_name(self, data):
        return validate_name(data)

    def validate_last_name(self, data):
        return validate_name(data)

    def validate_middle_name(self, data):
        return validate_name(data)

    def validate_phone_number(self, data):
        return validate_uz_phone_number(data)

    def validate_password(self, data):
        return validate_password(data)

    def validate(self, data):
        if data.get('password') and data.get('confirm_password'):
            if data['password'] != data['confirm_password']:
                raise serializers.ValidationError({"error": "Passwords do not match"})
            data.pop('confirm_password')
            data['password'] = make_password(data['password'])
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['role'] = dict(ROLE_CHOICES).get(instance.role, 'Unknown')
        data['academic_degree'] = dict(ACADEMIC_DEGREE).get(instance.academic_degree, 'Unknown')
        return data


class GetJurySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'middle_name', 'phone_number', 'birth_date',
                  'place_of_work', 'academic_degree',
                  'speciality']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        lang = request.headers.get('Accept-Language', settings.MODELTRANSLATION_DEFAULT_LANGUAGE)
        lang_options = settings.MODELTRANSLATION_LANGUAGES
        # data['academic_degree'] = dict(ACADEMIC_DEGREE).get(instance.academic_degree, 'Unknown')
        if lang in lang_options:
            data['place_of_work'] = getattr(instance, f'place_of_work_{lang}')
            data['speciality'] = getattr(instance.category, f'speciality_{lang}')
        return data


class GradeCriteriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeCriteria
        fields = ['id', 'criteria']


class CreateCompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = ['id', 'image', 'name', 'name_uz', 'name_ru', 'name_en', 'category',
                  'description', 'description_uz', 'description_ru', 'description_en',
                  'comp_start_date',
                  'comp_start_time',
                  'comp_end_date',
                  'comp_end_time', 'application_start_date', 'application_start_time',
                  'application_end_date', 'application_end_time', 'rules', 'status', 'prize', 'participation_fee',
                  'physical_certificate']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['category'] = instance.category.name
        data['status'] = dict(STATUS).get(instance.status, 'Unknown')
        return data


class ChildWorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChildWork
        fields = ['id', 'files']


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = ['grade']


class StatusParticipantSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField(source='get_full_name')
    date_of_birth = serializers.SerializerMethodField(source='get_date_of_birth')
    age = serializers.SerializerMethodField(source='get_age')
    study_place = serializers.SerializerMethodField(source='get_study_place')
    works = serializers.SerializerMethodField(source='get_works')
    grade = serializers.SerializerMethodField(source='get_grade')
    comment = serializers.SerializerMethodField(source='get_comment')

    class Meta:
        model = Participant
        fields = ['id', 'full_name', 'date_of_birth', 'age', 'study_place', 'works', 'grade']

    def get_works(self, obj):
        works_instance = ChildWork.objects.filter(
            participant__id=obj.id, competition__id=obj.competition.id
        )
        if works_instance:
            request = self.context.get('request')
            return ChildWorkSerializer(works_instance, many=True, context={'request': request}).data
        return None

    def get_grade(self, obj):
        grade_instance = Assessment.objects.filter(
            participant__id=obj.id, participant__competition__id=obj.competition.id
        ).first()
        if grade_instance:
            return grade_instance.grade
        return None

    def get_comment(self, obj):
        grade_instance = Assessment.objects.filter(
            participant__id=obj.id, participant__competition__id=obj.competition.id
        ).first()
        if grade_instance:
            return grade_instance.comment
        return None

    def get_full_name(self, obj):
        return f'{obj.child.first_name} {obj.child.last_name} {obj.child.middle_name}'

    def get_study_place(self, obj):
        return obj.child.place_of_study

    def get_date_of_birth(self, obj):
        return obj.child.date_of_birth

    def get_age(self, obj):
        today = date.today()
        birthdate = obj.child.date_of_birth
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        return age


class WinnerSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    birth_date = serializers.CharField(read_only=True)

    class Meta:
        model = Winner
        fields = ['id', 'competition', 'place', 'first_name', 'last_name', 'birth_date', 'email', 'phone_number',
                  'grade', 'jury_comment', 'certificate', 'address_for_physical_certificate', 'participant']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['place'] = dict(PLACE).get(instance.place, 'Unknown')
        return data

    def validate_phone_number(self, data):
        return validate_uz_phone_number(data)


class WinnerListSerializer(serializers.ModelSerializer):
    child = serializers.SerializerMethodField(source='get_child')
    works = serializers.SerializerMethodField(source='get_works')
    grade = serializers.SerializerMethodField(source='get_grade')

    class Meta:
        model = Winner
        fields = ['id', 'place', 'child', 'works', 'grade']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data

    def get_works(self, obj):
        works_instance = ChildWork.objects.filter(
            participant=obj.participant, competition__id=obj.competition.id
        )
        if works_instance:
            request = self.context.get('request')
            return ChildWorkSerializer(works_instance, many=True, context={'request': request}).data
        return None

    def get_grade(self, obj):
        grade_instance = Assessment.objects.filter(
            participant=obj.participant, participant__competition__id=obj.competition.id
        ).first()
        if grade_instance:
            return GradeSerializer(grade_instance).data
        return None

    def get_child(self, obj):
        child_instance = Child.objects.filter(id=obj.participant.child.id).first()
        if child_instance:
            return ChildSerializer(child_instance).data
        return None


class RegisterParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = ['id', 'competition', 'child', 'physical_certificate']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['competition'] = instance.competition.name
        data['child'] = instance.child.first_name
        return data


class PolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = Policy
        fields = ['id', 'description']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        lang = request.headers.get('Accept-Language', settings.MODELTRANSLATION_DEFAULT_LANGUAGE)
        lang_options = settings.MODELTRANSLATION_LANGUAGES
        if lang in lang_options:
            data['description'] = getattr(instance, f'description_{lang}')
        return data


class AboutUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutUs
        fields = ['id', 'title', 'sub_title', 'description', 'founder_name', 'founder_position', 'founder_image',
                  'co_founder_name', 'co_founder_position', 'co_founder_image']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        lang = request.headers.get('Accept-Language', settings.MODELTRANSLATION_DEFAULT_LANGUAGE)
        lang_options = settings.MODELTRANSLATION_LANGUAGES
        if lang in lang_options:
            data['title'] = getattr(instance, f'title_{lang}')
            data['sub_title'] = getattr(instance, f'sub_title_{lang}')
            data['description'] = getattr(instance, f'description_{lang}')
            data['founder_position'] = getattr(instance, f'founder_position_{lang}')
            data['co_founder_position'] = getattr(instance, f'co_founder_position_{lang}')
        return data


class AboutResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutResult
        fields = ['id', 'description', 'image']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        lang = request.headers.get('Accept-Language', settings.MODELTRANSLATION_DEFAULT_LANGUAGE)
        lang_options = settings.MODELTRANSLATION_LANGUAGES
        if lang in lang_options:
            data['description'] = getattr(instance, f'description_{lang}')
        return data


class ContactInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInformation
        fields = ['id', 'location', 'phone_number', 'email', 'image']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        lang = request.headers.get('Accept-Language', settings.MODELTRANSLATION_DEFAULT_LANGUAGE)
        lang_options = settings.MODELTRANSLATION_LANGUAGES
        if lang in lang_options:
            data['location'] = getattr(instance, f'location_{lang}')
        return data


class WebSocialMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialMedia
        fields = ['id', 'name', 'link', 'image']


class SpecialPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = Policy
        fields = ['id', 'description', 'description_uz', 'description_ru', 'description_en']


class SpecialAboutResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutResult
        fields = ['id', 'description', 'description_uz', 'description_ru', 'description_en', 'image']


class SpecialContactInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInformation
        fields = ['id', 'location', 'location_uz', 'location_ru', 'location_en', 'phone_number',
                  'email', 'image']

    def validate(self, attrs):
        phone_number = attrs['phone_number']
        validate_uz_phone_number(phone_number)
        return attrs


class SpecialAboutUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutUs
        fields = ['id', 'title', 'title_uz', 'title_ru', 'title_en', 'sub_title', 'sub_title_uz', 'sub_title_ru',
                  'sub_title_en', 'description', 'description_uz', 'description_ru', 'description_en', 'founder_name',
                  'founder_position', 'founder_position_uz', 'founder_position_ru', 'founder_position_en',
                  'founder_image',
                  'co_founder_name', 'co_founder_position', 'co_founder_position_uz', 'co_founder_position_ru',
                  'co_founder_position_en', 'co_founder_image']


#
class GetExistJurySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'middle_name', 'phone_number', 'birth_date',
                  'place_of_work', 'place_of_work_uz', 'place_of_work_ru', 'place_of_work_en', 'academic_degree',
                  'speciality', 'speciality_uz', 'speciality_ru', 'speciality_en', 'category',
                  'image', 'username']


class GetExistCompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = ['id', 'image', 'name', 'name_uz', 'name_ru', 'name_en', 'category',
                  'description', 'description_uz', 'description_ru', 'description_en',
                  'comp_start_date',
                  'comp_start_time',
                  'comp_end_date',
                  'comp_end_time', 'application_start_date', 'application_start_time',
                  'application_end_date', 'application_end_time', 'rules', 'status']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['category'] = instance.category.name
        data['status'] = dict(STATUS).get(instance.status, 'Unknown')
        return data


class GetExistContactInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInformation
        fields = ['id', 'location', 'location_uz', 'location_ru', 'location_en', 'phone_number',
                  'email', 'image']


class GetExistPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = Policy
        fields = ['id', 'description', 'description_uz', 'description_ru', 'description_en']


class GetExistAboutUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutUs
        fields = ['id', 'title', 'title_uz', 'title_ru', 'title_en', 'sub_title', 'sub_title_uz', 'sub_title_ru',
                  'sub_title_en', 'description', 'description_uz', 'description_ru', 'description_en', 'founder_name',
                  'founder_position', 'founder_position_uz', 'founder_position_ru', 'founder_position_en',
                  'founder_image',
                  'co_founder_name', 'co_founder_position', 'co_founder_position_uz', 'co_founder_position_ru',
                  'co_founder_position_en', 'co_founder_image']


class GetExistAboutResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutResult
        fields = ['id', 'description', 'description_uz', 'description_ru', 'description_en', 'image']


class ExistWinnerSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    birth_date = serializers.CharField(read_only=True)

    class Meta:
        model = Winner
        fields = ['id', 'place', 'first_name', 'last_name', 'birth_date', 'email', 'phone_number',
                  'grade', 'jury_comment', 'certificate', 'address_for_physical_certificate']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['place'] = dict(PLACE).get(instance.place, 'Unknown')
        data['first_name'] = instance.participant.child.first_name
        data['last_name'] = instance.participant.child.last_name
        data['birth_date'] = instance.participant.child.date_of_birth
        return data


#
class ForUpdateWinnerSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    birth_date = serializers.CharField(read_only=True)

    class Meta:
        model = Winner
        fields = ['id', 'place', 'first_name', 'last_name', 'birth_date', 'email', 'phone_number',
                  'grade', 'jury_comment', 'certificate', 'address_for_physical_certificate', 'participant']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get('place'):
            data['place'] = dict(PLACE).get(instance.place, 'Unknown')
        return data

    def validate(self, data):
        if data.get('place'):
            winner = Winner.objects.filter(place=data['place']).first()
            if winner:
                raise serializers.ValidationError(
                    _("You've already created %(place)s place") % {'place': data['place']})
        return data

    def validate_phone_number(self, data):
        return validate_uz_phone_number(data)


class GetForUpdateWinnerSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    birth_date = serializers.CharField(read_only=True)

    class Meta:
        model = Winner
        fields = ['id', 'place', 'first_name', 'last_name', 'birth_date', 'email', 'phone_number',
                  'grade', 'jury_comment', 'certificate', 'address_for_physical_certificate']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['place'] = dict(PLACE).get(instance.place, 'Unknown')
        return data


class UpdateJurySerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    confirm_password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'middle_name', 'phone_number', 'birth_date',
                  'place_of_work', 'place_of_work_uz', 'place_of_work_ru', 'place_of_work_en', 'academic_degree',
                  'speciality', 'speciality_uz', 'speciality_ru', 'speciality_en', 'category', 'username', 'password',
                  'confirm_password', 'image']

    def validate_first_name(self, data):
        return validate_name(data)

    def validate_last_name(self, data):
        return validate_name(data)

    def validate_middle_name(self, data):
        return validate_name(data)

    def validate_phone_number(self, data):
        return validate_uz_phone_number(data)

    def validate_password(self, data):
        return validate_password(data)

    def validate(self, data):
        if data.get('password') and data.get('confirm_password'):
            if data['password'] != data['confirm_password']:
                raise serializers.ValidationError({"error": _("Passwords do not match")})
            data.pop('confirm_password')
            data['password'] = make_password(data['password'])
        return data


class GetExistCompetitionByIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = ['id', 'image', 'name', 'name_uz', 'name_ru', 'name_en', 'category', 'description',
                  'description_uz', 'description_ru', 'description_en', 'comp_start_date', 'comp_start_time',
                  'comp_end_date', 'comp_end_time', 'application_start_date', 'application_start_time',
                  'application_end_date', 'application_end_time', 'rules', 'status', 'physical_certificate', 'prize',
                  'participation_fee']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['category'] = instance.category.name
        data['status'] = dict(STATUS).get(instance.status, 'Unknown')
        return data


class DownloadCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Winner
        fields = ['certificate']


class PurchaseInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseModel
        fields = ['competition', 'participant', 'price']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['participant'] = f'{instance.participant.child.first_name} {instance.participant.child.last_name}'
        request = self.context.get('request')
        lang = request.headers.get('Accept-Language', settings.MODELTRANSLATION_DEFAULT_LANGUAGE)
        lang_options = settings.MODELTRANSLATION_LANGUAGES
        if lang in lang_options:
            data['competition'] = getattr(instance.competition, f'name_{lang}')
        else:
            data['competition'] = instance.competition.name
        return data
