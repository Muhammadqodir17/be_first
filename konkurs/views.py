from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from jury.models import Assessment
from jury.serializers import AssessmentHistorySerializer
from authentication.models import User
from konkurs_admin.models import (
    Notification,
    Winner,
    WebCertificate,
    ResultImage,
    Policy,
    AboutUs,
    AboutResult,
    ContactInformation,
    SocialMedia, SubscriptionModel
)
from konkurs_admin.serializers import (
    PolicySerializer,
    AboutUsSerializer,
    AboutResultSerializer,
    ContactInformationSerializer,
    WebSocialMediaSerializer
)
from .serializers import (
    HomeCompetitionSerializer,
    CompParticipantSerializer,
    ActiveParticipantSerializer,
    FinishedParticipantSerializer,
    CompetitionForCompetitionPageSerializer,
    GallerySerializer,
    GalleryDetailsSerializer,
    ExpertSerializer,
    BannerSerializer,
    NotificationSerializer,
    ResultsSerializer,
    GetCompSerializer,
    ContactUsSerializer,
    ResultImageSerializer,
    WebCerSerializer,
    GetSubscriptionsSerializer,
    SubscribeCompetitionSerializer,
)
from .models import (
    Competition,
    Participant,
    ChildWork,
)
from django.utils.translation import gettext_lazy  as _


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
        banner = Competition.objects.filter().order_by('-created_at').first()
        serializer = BannerSerializer(banner, context={'request': request})
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
        home_comps = Competition.objects.filter(status=1)
        serializer = HomeCompetitionSerializer(home_comps, many=True, context={'request': request})
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
        serializer = CompetitionForCompetitionPageSerializer(comp, many=True, context={'request': request})
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
        works = ChildWork.objects.filter(participant__action=2)
        serializer = GallerySerializer(works, many=True, context={'request': request})
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
        serializer = ExpertSerializer(experts, many=True, context={'request': request})
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
        certificate_obj = WebCertificate.objects.all().first()
        if certificate_obj:
            certificate = certificate_obj.data.year if certificate_obj.data else 0
            cer_serializer = WebCerSerializer(certificate_obj, context={'request': request})
        else:
            certificate = 0
            cer_serializer = ''
        creative_works = 0
        images = ResultImage.objects.all()

        serialized_images = ResultImageSerializer(images, many=True, context={'request': request})

        result_data = {
            "participants": participants,
            "winners": winners,
            "awards": awards,
            "certificate": certificate,
            "certificate_image": cer_serializer.data,
            "creative_works": creative_works,
            "images": serialized_images.data
        }
        return Response(data=result_data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get competition by id",
        operation_summary="Get competition by id",
        responses={
            200: GetCompSerializer(),
        },
        tags=['competition']
    )
    def get_by_id(self, request, *args, **kwargs):
        comp = Competition.objects.filter(id=kwargs['pk']).first()
        if comp is None:
            return Response(data={'error': _('Comp not found')}, status=status.HTTP_404_NOT_FOUND)
        serializer = GetCompSerializer(comp, context={'request': request})
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
            return Response(data={'error': _('Participant not found')}, status=status.HTTP_200_OK)
        serializer = GalleryDetailsSerializer(participant, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class MyCompetitionViewSet(ViewSet):
    @swagger_auto_schema(
        operation_description="Get comp details",
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
        participant = Participant.objects.filter(competition__id=kwargs['pk']).first()
        if participant is None:
            return Response(data={'error': _('Not found')}, status=status.HTTP_404_NOT_FOUND)
        if participant.competition.status == 2:
            serializer = FinishedParticipantSerializer(participant, context={'request': request})
        elif participant.competition.status == 1:
            serializer = ActiveParticipantSerializer(participant, context={'request': request})
        else:
            return Response(data={'error': _('Comp is not active')}, status=status.HTTP_400_BAD_REQUEST)
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
        serializer = CompParticipantSerializer(participants, many=True, context={'request': request})
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
        serializer = CompParticipantSerializer(participants, many=True, context={'request': request})
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
        serializer = AssessmentHistorySerializer(grades, many=True, context={'request': request})
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
            return Response(data={'error': _('Assessment not found')}, status=status.HTTP_404_NOT_FOUND)
        serializer = AssessmentHistorySerializer(grade, context={'request': request})
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
        user = User.objects.filter(id=request.user.id).first()
        if user is None:
            return Response(data={'error': _('User not found')}, status=status.HTTP_404_NOT_FOUND)
        notifications = Notification.objects.filter(user=user)
        serializer = NotificationSerializer(notifications, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get Notification By Id For Comp",
        operation_summary="Get all Notification By Id For Comp",
        responses={
            200: NotificationSerializer(),
        },
        tags=['competition']
    )
    def get_notification_by_id(self, request, *args, **kwargs):
        notification = Notification.objects.filter(id=kwargs['pk']).first()
        if notification is None:
            return Response(data={'error': _('Notification not found')}, status=status.HTTP_404_NOT_FOUND)
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        serializer = NotificationSerializer(notification, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class ContactUsViewSet(ViewSet):
    @swagger_auto_schema(
        operation_description="Contact Us",
        operation_summary="Contact Us",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='email'),
            },
            required=['name']
        ),
        responses={201: ContactUsSerializer()},
        tags=['competition'],
    )
    def create(self, request, *args, **kwargs):
        serializer = ContactUsSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


class DynamicInfoViewSet(ViewSet):
    @swagger_auto_schema(
        operation_description="Get all Result Image",
        operation_summary="Get all Result Image",
        responses={
            200: ResultImageSerializer(),
        },
        tags=['competition']
    )
    def get_web_result_image(self, request, *args, **kwargs):
        web_res = ResultImage.objects.all()
        serializer = ResultImageSerializer(web_res, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get all Policy",
        operation_summary="Get all Policy",
        responses={
            200: PolicySerializer(),
        },
        tags=['competition']
    )
    def get_all_policy(self, request, *args, **kwargs):
        policy = Policy.objects.all()
        serializer = PolicySerializer(policy, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get all About Us",
        operation_summary="Get all About Us",
        responses={
            200: AboutUsSerializer(),
        },
        tags=['competition']
    )
    def get_all_about_us(self, request, *args, **kwargs):
        about_us = AboutUs.objects.all()
        serializer = AboutUsSerializer(about_us, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get all About Result",
        operation_summary="Get all About Result",
        responses={
            200: AboutResultSerializer(),
        },
        tags=['competition']
    )
    def get_all_about_result(self, request, *args, **kwargs):
        about_result = AboutResult.objects.all()
        serializer = AboutResultSerializer(about_result, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get all Contact Info",
        operation_summary="Get all Contact Info",
        responses={
            200: ContactInformationSerializer(),
        },
        tags=['competition']
    )
    def get_all_contact_info(self, request, *args, **kwargs):
        contact_info = ContactInformation.objects.all()
        serializer = ContactInformationSerializer(contact_info, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get all Social Media",
        operation_summary="Get Social Media",
        responses={
            200: WebSocialMediaSerializer(),
        },
        tags=['competition']
    )
    def get_all_social_media(self, request, *args, **kwargs):
        social_media = SocialMedia.objects.all()
        serializer = WebSocialMediaSerializer(social_media, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class SubscriptionViewSet(ViewSet):
    @swagger_auto_schema(
        operation_description="Get all Subscriptions",
        operation_summary="Get all Subscriptions",
        responses={
            200: GetSubscriptionsSerializer(),
        },
        tags=['competition']
    )
    def get_all(self, request, *args, **kwargs):
        user = request.user
        competition = SubscriptionModel.objects.filter(user=user)
        serializer = GetSubscriptionsSerializer(competition, many=True)
        return Response(data=serializer.data)

    @swagger_auto_schema(
        operation_description="Subscribe",
        operation_summary="Subscribe",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'competition': openapi.Schema(type=openapi.TYPE_INTEGER, description='competition'),
            },
            required=['competition']
        ),
        responses={200: SubscribeCompetitionSerializer()},
        tags=['competition'],
    )
    def subscription(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        subs = SubscriptionModel.objects.filter(user=request.user, competition=request.data['competition']).first()
        if subs.exist():
            return Response(data={'error': _('You already subscribe this competition')}, status=status.HTTP_400_BAD_REQUEST)
        serializer = SubscribeCompetitionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Unsubscribe",
        operation_summary="Unsubscribe",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'competition': openapi.Schema(type=openapi.TYPE_INTEGER, description='competition'),
            },
            required=['competition']
        ),
        responses={200: 'Successfully Unsubscribed'},
        tags=['competition'],
    )
    def unsubscription(self, request, *args, **kwargs):
        subs = SubscriptionModel.objects.filter(user=request.user, competition=request.data['competition']).first()
        if subs is None:
            return Response(data={'error': _('You did not subscribe this competition')}, status=status.HTTP_400_BAD_REQUEST)
        subs.delete()
        return Response(data={'message': _('Successfully Unsubscribed')}, status=status.HTTP_200_OK)

