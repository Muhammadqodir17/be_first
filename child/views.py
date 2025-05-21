from rest_framework.viewsets import ViewSet
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from authentication.models import User
from rest_framework.response import Response
from rest_framework import status
from konkurs.serializers import (
    ChildrenSerializer,
    GetRegisteredChild
)
from .serializers import (
    ChildSerializer,
    ChildWorkSerializer,
)
from .models import Child
from rest_framework.parsers import MultiPartParser
from konkurs_admin.serializers import (
    RegisterParticipantSerializer
)
from konkurs.models import (
    ChildWork,
    Participant,
    Competition
)
from django.utils.translation import gettext_lazy  as _

""" payment """
from click_up import ClickUp
from django.conf import settings

click_up = ClickUp(
    service_id=settings.CLICK_SERVICE_ID,
    merchant_id=settings.CLICK_MERCHANT_ID
)
""" """


class ChildViewSet(ViewSet):
    @swagger_auto_schema(
        operation_description="Get user children",
        operation_summary="Get user children",
        responses={
            200: ChildrenSerializer(),
        },
        tags=['child']
    )
    def get_user_children(self, request, *args, **kwargs):
        children = Child.objects.filter(user=request.user)
        serializer = ChildrenSerializer(children, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get user child registered to comp",
        operation_summary="Get user child registered to comp",
        responses={
            200: GetRegisteredChild(),
        },
        tags=['child']
    )
    def get_registered_child(self, request, *args, **kwargs):
        comp = Competition.objects.filter(id=kwargs['pk']).first()
        if comp is None:
            return Response(data={'error': _('Comp is not found')}, status=status.HTTP_404_NOT_FOUND)
        participants = Participant.objects.filter(child__user=request.user, competition=comp)
        serializer = GetRegisteredChild(participants, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Foydalanuvchiga tegishli barcha bolalarni olish",
        responses={200: ChildSerializer(many=True)}
    )
    def list(self, request):
        children = Child.objects.filter(user=request.user)
        serializer = ChildSerializer(children, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Foydalanuvchiga tegishli ma'lum bir bolani ID orqali olish",
        responses={200: ChildSerializer()}
    )
    def retrieve(self, request, pk=None):
        try:
            child = Child.objects.get(id=pk, user=request.user)
            serializer = ChildSerializer(child)
            return Response(serializer.data)
        except Child.DoesNotExist:
            return Response({'error': _('Bola topilmadi')}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The first name of the child.",
                ),
                'last_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The last name of the child.",
                ),
                'middle_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The middle name of the child.",
                ),
                'date_of_birth': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The birth date of the child.",
                ),
                'place_of_study': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="place_of_study",
                ),

                'degree_of_kinship': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="degree_of_kinship",
                ),
            },
            required=['first_name', 'last_name', 'middle_name', 'birth_date', 'place_of_study', 'degree_of_kinship'],
        ),
        responses={
            201: ChildSerializer()
        },
        operation_summary="Create a child",
        operation_description='Create a child'
    )
    def create(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        user = User.objects.filter(id=request.user.id).first()
        if user is None:
            return Response(data={'error': _('User not found')}, status=status.HTTP_404_NOT_FOUND)
        if user.children_count >= 5:
            return Response({'message': _('You have already registered 5 children')},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = ChildSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=user)
            user.children_count += 1
            user.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Bola ma'lumotlarini yangilash",
        request_body=ChildSerializer,
        responses={200: ChildSerializer()}
    )
    def update(self, request, pk=None):
        try:
            child = Child.objects.get(id=pk, user=request.user)
        except Child.DoesNotExist:
            return Response({'error': _('Bola topilmadi')}, status=status.HTTP_404_NOT_FOUND)

        serializer = ChildSerializer(child, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Bola ma'lumotlarini o'chirish",
        responses={204: 'Bola muvaffaqiyatli o\'chirildi'}
    )
    def delete(self, request, pk=None):
        try:
            child = Child.objects.get(id=pk, user=request.user)
            child.delete()
            return Response({'message': _('Bola muvaffaqiyatli o\'chirildi')}, status=status.HTTP_204_NO_CONTENT)
        except Child.DoesNotExist:
            return Response({'error': _('Bola topilmadi')}, status=status.HTTP_404_NOT_FOUND)


class RegisterChildToCompViewSet(ViewSet):
    @swagger_auto_schema(
        operation_description="Register Child To Comp",
        operation_summary="Register Child To Comp",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'child': openapi.Schema(type=openapi.TYPE_INTEGER, description='child'),
                'competition': openapi.Schema(type=openapi.TYPE_INTEGER, description='competition'),
                'physical_certificate': openapi.Schema(type=openapi.TYPE_BOOLEAN,
                                                       description='physical_certificate'),
            },
            required=['child', 'competition', 'physical_certificate']
        ),
        responses={201: RegisterParticipantSerializer()},
        tags=['child'],
    )
    def create(self, request, *args, **kwargs):
        serializer = RegisterParticipantSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


class ChildWorkViewSet(ViewSet):  # *
    parser_classes = [MultiPartParser]

    @swagger_auto_schema(
        operation_description="Upload work files",
        operation_summary="Upload work files",
        manual_parameters=[
            openapi.Parameter(
                name='participant',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_INTEGER,
                required=True,
                description="Participant ID"
            ),
            openapi.Parameter(
                name='files',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="Files to upload",
            ),
        ],
        responses={201: ChildWorkSerializer()},
        tags=['child'],
    )
    def create(self, request, *args, **kwargs):
        participant = Participant.objects.filter(id=request.data['participant']).first()
        if participant is None:
            return Response(data={'error': _('Participant not found')}, status=status.HTTP_404_NOT_FOUND)
        serializer = ChildWorkSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        files = request.FILES.getlist('files')
        ChildWork.objects.bulk_create([
            ChildWork(participant=participant, competition=participant.competition, files=file)
            for file in files
        ])
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)
