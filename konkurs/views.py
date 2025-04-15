from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from jury.models import Assessment
from jury.serializers import AssessmentHistorySerializer

from authentication.models import User
from konkurs_admin.models import Notification, Winner
from .serializers import (
    CompetitionSerializer,
    HomeCompetitionSerializer,
    CompParticipantSerializer,
    ActiveParticipantSerializer,
    FinishedParticipantSerializer,
    CompetitionForCompetitionPageSerializer,
    GallerySerializer,
    GalleryDetailsSerializer,
    ExpertSerializer,
    BannerSerializer,
    NotificationSerializer, ResultsSerializer
)
from .models import (
    Competition,
    Participant,
    ChildWork,
)


class CompetitionViewSet(ViewSet):
    @swagger_auto_schema(
        operation_description="Get Main Banner",
        operation_summary="Get Main Banner",
        responses={
            200: BannerSerializer(),
        },
        tags=['competition']
    )
    def get_main_banner(self, request, *args, **kwargs):
        banner = Competition.objects.filter().order_by('created_at').first()
        serializer = BannerSerializer(banner)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get All Competition For Home Page",
        operation_summary="Get All Competition For Home Page",
        responses={
            200: HomeCompetitionSerializer(),
        },
        tags=['competition']
    )
    def get_comp_for_home(self, request, *args, **kwargs):
        home_comps = Competition.objects.all()
        serializer = HomeCompetitionSerializer(home_comps, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get All Competition For Competition Page",
        operation_summary="Get All Competition For Competition Page",
        responses={
            200: CompetitionForCompetitionPageSerializer(),
        },
        tags=['competition']
    )
    def get_comp(self, request, *args, **kwargs):
        comp = Competition.objects.all()
        serializer = CompetitionForCompetitionPageSerializer(comp, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get Gallery",
        operation_summary="Get Gallery",
        responses={
            200: GallerySerializer(),
        },
        tags=['competition']
    )
    def get_gallery(self, request, *args, **kwargs):
        works = ChildWork.objects.all()
        serializer = GallerySerializer(works, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get All Experts",
        operation_summary="Get All Experts",
        responses={
            200: ExpertSerializer(),
        },
        tags=['competition']
    )
    def get_experts(self, request, *args, **kwargs):
        experts = User.objects.filter(role=2)
        serializer = ExpertSerializer(experts, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get Results",
        operation_summary="Get Results",
        responses={
            200: ResultsSerializer(),
        },
        tags=['competition']
    )
    def get_results(self, request, *args, **kwargs):
        participants = Participant.objects.all().count()
        winners = Winner.objects.filter(place=1).count()
        awards = 0
        certificates = 0
        creative_works = 0

        serializer = ResultsSerializer({
            "participants": participants,
            "winners": winners,
            "awards": awards,
            "certificates": certificates,
            "creative_works": creative_works
        })
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get competition details",
        operation_summary="Get competition details",
        responses={
            200: CompetitionSerializer(),
        },
        tags=['competition']
    )
    def get_by_id(self, request, *args, **kwargs):
        comp = Competition.objects.filter(id=kwargs['pk']).first()
        serializer = CompetitionSerializer(comp)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get Gallery By Id",
        operation_summary="Get Gallery By Id",
        responses={
            200: GalleryDetailsSerializer(),
        },
        tags=['competition']
    )
    def get_gallery_details(self, request, *args, **kwargs):
        participant = Participant.objects.filter(id=kwargs['pk']).first()
        if participant is None:
            return Response(data={'error': 'Participant not found'}, status=status.HTTP_200_OK)
        serializer = GalleryDetailsSerializer(participant)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class MyCompetitionViewSet(ViewSet):
    @swagger_auto_schema(
        operation_description="Get comp details by id",
        operation_summary="active or finished",
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'competition': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Competition ID"),
                            'name': openapi.Schema(type=openapi.TYPE_STRING, description="Competition Name"),
                            'description': openapi.Schema(type=openapi.TYPE_STRING,
                                                          description="Competition Description"),
                            'participants': openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                description="Number of participants (only for active competitions)",
                                nullable=True
                            ),
                            'application_end_date': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                format="date",
                                description="Competition end date (only for active competitions)",
                                nullable=True
                            ),
                        },
                        description="Competition details (varies based on status)"
                    ),
                    'grade': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Grade ID"),
                            'score': openapi.Schema(type=openapi.TYPE_INTEGER, description="Score awarded"),
                            'comments': openapi.Schema(type=openapi.TYPE_STRING, description="Feedback comments"),
                        },
                        description="Grade details (only for finished competitions)",
                        nullable=True
                    )
                },
            ),
        },
        tags=['competition']
    )
    def get_comp_details(self, request, *args, **kwargs):
        participant = Participant.objects.filter(id=kwargs['pk']).first()
        if participant is None:
            return Response(data={'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        if participant.competition.status == 1:
            serializer = ActiveParticipantSerializer(participant)
        else:
            serializer = FinishedParticipantSerializer(participant)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get Active Competitions",
        operation_summary="Get Active Competitions",
        responses={
            200: CompParticipantSerializer(),
        },
        tags=['competition']
    )
    def active(self, request, *args, **kwargs):
        participants = Participant.objects.filter(child__user=request.user, competition__status=1)
        serializer = CompParticipantSerializer(participants, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get Finished Competitions",
        operation_summary="Get Finished Competitions",
        responses={
            200: CompParticipantSerializer(),
        },
        tags=['competition']
    )
    def finished(self, request, *args, **kwargs):
        participants = Participant.objects.filter(child__user=request.user, competition__status=2)
        serializer = CompParticipantSerializer(participants, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get Grade History",
        operation_summary="Get Grade History",
        responses={
            200: AssessmentHistorySerializer(),
        },
        tags=['competition']
    )
    def get_grade_history(self, request, *args, **kwargs):
        grades = Assessment.objects.filter(participant__child__user=request.user)
        serializer = AssessmentHistorySerializer(grades, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get Grade By Id For Comp",
        operation_summary="Get Grade By Id For Comp",
        responses={
            200: AssessmentHistorySerializer(),
        },
        tags=['competition']
    )
    def get_grade_history_by_id(self, request, *args, **kwargs):
        grade = Assessment.objects.filter(participant__child__user=request.user, id=kwargs['pk']).first()
        if grade is None:
            return Response(data={'error': 'Assessment not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AssessmentHistorySerializer(grade)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get Notifications For Comp",
        operation_summary="Get Notifications For Comp",
        responses={
            200: NotificationSerializer(),
        },
        tags=['competition']
    )
    def get_notifications(self, request, *args, **kwargs):
        notifications = Notification.objects.all()
        serializer = NotificationSerializer(notifications, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get Notification By Id For Comp",
        operation_summary="Get all competition By Id For Comp",
        responses={
            200: NotificationSerializer(),
        },
        tags=['competition']
    )
    def get_notification_by_id(self, request, *args, **kwargs):
        notification = Notification.objects.filter(id=kwargs['pk']).first()
        if notification is None:
            return Response(data={'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        serializer = NotificationSerializer(notification)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
