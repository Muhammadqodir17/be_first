from codecs import replace_errors
from datetime import date
from rest_framework import serializers
from jury.models import Assessment
from konkurs.models import (
    Category,
    Competition,
    Participant,
    APPROVEMENT,
    MARKED_STATUS,
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
from .models import (
    Winner,
    PLACE
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class GetCompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = ['id', 'name', 'category', 'description', 'application_start_date', 'application_start_time',
                  'application_end_date', 'application_end_time', 'status', 'rules', 'participation_fee', 'image',
                  'prize']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['status'] = dict(STATUS).get(instance.status, 'Unknown')
        data['category'] = instance.category.name
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
    child = ChildSerializer()
    works = serializers.SerializerMethodField(source='get_works')

    class Meta:
        model = Participant
        fields = ['id', 'child', 'action', 'works', 'physical_certificate', 'marked_status']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['action'] = dict(APPROVEMENT).get(instance.action, 'Unknown')
        data['marked_status'] = dict(MARKED_STATUS).get(instance.marked_status, 'Unknown')
        return data

    def get_works(self, obj):
        works_instance = ChildWork.objects.filter(participant=obj, competition__id=obj.competition.id)
        if works_instance:
            return ChildWorkSerializer(works_instance, many=True).data
        return None


# for create
class JurySerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'middle_name', 'phone_number', 'birth_date',
                  'place_of_work', 'academic_degree', 'speciality', 'category', 'username', 'password',
                  'confirm_password', 'role']

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
        fields = ['id', 'first_name', 'last_name', 'middle_name', 'birth_date', 'place_of_work', 'academic_degree',
                  'speciality']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['academic_degree'] = dict(ACADEMIC_DEGREE).get(instance.academic_degree, 'Unknown')
        return data


class GradeCriteriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeCriteria
        fields = ['id', 'criteria']


class CompetitionSerializer(serializers.ModelSerializer):
    criteria = serializers.SerializerMethodField(source='get_criteria')

    class Meta:
        model = Competition
        fields = ['id', 'name', 'category', 'description', 'comp_start_date', 'comp_start_time', 'comp_end_date',
                  'comp_end_time', 'application_start_date', 'application_start_time',
                  'application_end_date', 'application_end_time', 'status', 'rules', 'participation_fee', 'image',
                  'prize', 'criteria']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['status'] = dict(STATUS).get(instance.status, 'Unknown')
        return data

    def get_criteria(self, obj):
        criteria_instance = GradeCriteria.objects.filter(competition__id=obj.id)
        if criteria_instance:
            return GradeCriteriaSerializer(criteria_instance, many=True).data
        return None


class ChildWorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChildWork
        fields = ['id', 'files']


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = ['id', 'grade']


class ActiveParticipantSerializer(serializers.ModelSerializer):
    child = ChildSerializer()
    works = serializers.SerializerMethodField(source='get_works')
    grade = serializers.SerializerMethodField(source='get_grade')

    class Meta:
        model = Participant
        fields = ['id', 'child', 'works', 'grade']

    def get_works(self, obj):
        works_instance = ChildWork.objects.filter(participant=obj, competition__id=obj.competition.id)
        if works_instance:
            return ChildWorkSerializer(works_instance, many=True).data
        return None

    def get_grade(self, obj):
        grade_instance = Assessment.objects.filter(participant=obj,
                                                   participant__competition__id=obj.competition.id).first()
        if grade_instance:
            return GradeSerializer(grade_instance).data
        return None


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


class WinnerListSerializer(serializers.ModelSerializer):
    child = serializers.SerializerMethodField(source='get_child')
    works = serializers.SerializerMethodField(source='get_works')
    grade = serializers.SerializerMethodField(source='get_grade')

    class Meta:
        model = Winner
        fields = ['id', 'place', 'child', 'works', 'grade']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['place'] = dict(PLACE).get(instance.place, 'Unknown')
        return data

    def get_works(self, obj):
        works_instance = ChildWork.objects.filter(
            participant=obj.participant, competition__id=obj.competition.id
        )
        if works_instance:
            return ChildWorkSerializer(works_instance, many=True).data
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

# class CreateCriteriaSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Criteria
#         fields = ['id', 'competition', 'name']
#
#
# class CreateCompSerializer(serializers.ModelSerializer):
#     criteria = serializers.ListSerializer(child=CreateCriteriaSerializer())
#     class Meta:
#         model = Competition
#         fields = ['id', 'name', 'category', 'description', 'prize', 'application_start_date',
#                   'application_start_time', 'application_end_date', 'application_end_time',
#                   'participation_fee', 'rules', 'physical_certificate', 'image', 'criteria']
class RegisterParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = ['id', 'competition', 'child', 'physical_certificate']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['competition'] = instance.competition.name
        data['child'] = instance.child.first_name
        return data
