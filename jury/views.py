from rest_framework.viewsets import ViewSet
from konkurs.models import (
    Competition,
    Participant, Category
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Assessment
from .serializers import (
    ActiveCompetitionSerializer,
    CompetitionSerializer,
    ParticipantWorkSerializer,
    MarkSerializer,
    AssessmentHistorySerializer,
    ParticipantSerializer,
)
from rest_framework.response import Response
from rest_framework import status
from authentication.models import User
from django.utils.translation import gettext_lazy  as _


class JuryViewSet(ViewSet):
    @swagger_auto_schema(
        operation_description="Active Competitions",
        operation_summary="Active Competitions",
        responses={
            200: ActiveCompetitionSerializer(),
        },
        tags=['jury']
    )
    def get_active_comp(self, request, *args, **kwargs):
        comps = Competition.objects.filter(status=1)
        serializer = ActiveCompetitionSerializer(comps, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Active Competitions if filter none",
        operation_summary="Active Competitions if filter none",
        responses={
            200: ActiveCompetitionSerializer(),
        },
        tags=['jury']
    )
    def get_active_comps(self, request, *args, **kwargs):
        user = User.objects.filter(id=request.user.id).first()
        if user is None:
            return Response(data={'error': _('User not found')})
        comps = Competition.objects.filter(status=1, category=user.category)
        serializer = ActiveCompetitionSerializer(comps, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Filter comp by Category",
        operation_summary="Filter comp by Category",
        manual_parameters=[
            openapi.Parameter(
                'category', type=openapi.TYPE_INTEGER, description='filter_category', in_=openapi.IN_QUERY
            )
        ],
        responses={200: ActiveCompetitionSerializer()},
        tags=['jury'],
    )
    def filter_comp(self, request, *args, **kwargs):
        data = request.GET
        category = data.get('category')
        competitions = Competition.objects.all()
        if category:
            competitions = Competition.objects.filter(category=category, status=1)
        serializer = ActiveCompetitionSerializer(competitions, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get Competition By Id",
        operation_summary="Get Competition By Id",
        responses={
            200: CompetitionSerializer(),
        },
        tags=['jury']
    )
    def get_comp_by_id(self, request, *args, **kwargs):
        comp = Competition.objects.filter(id=kwargs['pk']).first()
        if comp is None:
            return Response(data={'error': _('Competition not found')}, status=status.HTTP_404_NOT_FOUND)
        serializer = CompetitionSerializer(comp, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Filter Participants",
        operation_summary="Filter Participants",
        manual_parameters=[
            openapi.Parameter(
                'category', type=openapi.TYPE_STRING, description='filter_participants', in_=openapi.IN_QUERY
            )
        ],
        responses={200: ParticipantSerializer()},
        tags=['jury'],
    )
    def filter_participants(self, request, *args, **kwargs):
        category = request.GET.get('category')
        category = Category.objects.filter(id=category).first()
        if category is None:
            return Response(data={'error': _('Category not found')}, status=status.HTTP_404_NOT_FOUND)
        comp = Competition.objects.filter(id=kwargs['pk']).first()
        if comp is None:
            return Response(data={'error': _('Competition not found')}, status=status.HTTP_404_NOT_FOUND)
        participant = Participant.objects.filter(competition=comp, competition__category=category)
        serializer = ParticipantSerializer(participant, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get Participant By Id",
        operation_summary="Get Participant By Id",
        responses={
            200: ParticipantWorkSerializer(),
        },
        tags=['jury']
    )
    def get_participant_by_id(self, request, *args, **kwargs):
        participant = Participant.objects.filter(id=kwargs['pk']).first()
        if participant is None:
            return Response(data={'error': _('Participant not found')}, status=status.HTTP_404_NOT_FOUND)
        serializer = ParticipantWorkSerializer(participant, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Put Mak",
        operation_summary="Put Mark",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'participant': openapi.Schema(type=openapi.TYPE_INTEGER, description='participant'),
                'grade': openapi.Schema(type=openapi.TYPE_INTEGER, description='grade'),
                'comment': openapi.Schema(type=openapi.TYPE_STRING, description='comment'),
            },
            required=['jury', 'participant', 'grade', 'comment']
        ),
        responses={201: MarkSerializer()},
        tags=['jury'],
    )
    def mark(self, request, *args, **kwargs):
        request.data['jury'] = request.user.id
        participant = Participant.objects.filter(id=request.data['participant']).first()
        if participant is None:
            return Response(data={'error': _('Participant not found')}, status=status.HTTP_404_NOT_FOUND)
        serializer = MarkSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        if participant.marked_status == 2:
            return Response(data={'error': _("You've already marked this participant")},
                            status=status.HTTP_400_BAD_REQUEST)
        participant.marked = 2
        participant.save()
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Get Grade",
        operation_summary="Get Grade",
        responses={
            200: AssessmentHistorySerializer(),
        },
        tags=['jury']
    )
    def get_assessment_history(self, request, *args, **kwargs):
        assessment = Assessment.objects.filter(jury=request.user)
        serializer = AssessmentHistorySerializer(assessment, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get Grade By Id",
        operation_summary="Get Grade By Id",
        responses={
            200: AssessmentHistorySerializer(),
        },
        tags=['jury']
    )
    def get_assessment_by_id(self, request, *args, **kwargs):
        assessment = Assessment.objects.filter(id=kwargs['pk']).first()
        if assessment is None:
            return Response(data={'error': _('Assessment not found')}, status=status.HTTP_404_NOT_FOUND)
        serializer = AssessmentHistorySerializer(assessment, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Upload Mark",
        operation_summary="Upload Mark",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'participant': openapi.Schema(type=openapi.TYPE_INTEGER, description='participant'),
                'grade': openapi.Schema(type=openapi.TYPE_INTEGER, description='grade'),
                'comment': openapi.Schema(type=openapi.TYPE_STRING, description='comment'),
            },
            required=[]
        ),
        responses={200: AssessmentHistorySerializer()},
        tags=['jury'],
    )
    def update_assessment_history(self, request, *args, **kwargs):
        assessment = Assessment.objects.filter(id=kwargs['pk']).first()
        request.data['jury'] = request.user
        if assessment is None:
            return Response(data={'error': _('Assessment not found')}, status=status.HTTP_404_NOT_FOUND)
        serializer = AssessmentHistorySerializer(assessment, data=request.data, partial=True,
                                                 context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        if assessment.competition.status == 2:
            return Response(data={'error': _('You can not change this grade because Competition is '
                                             'finished')}, status=status.HTTP_400_BAD_REQUEST)
        if assessment.jury.id != request.user.id:
            return Response(data={'error': _('You can not change this grade')},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)
