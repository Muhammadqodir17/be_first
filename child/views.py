from rest_framework.viewsets import ViewSet
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from authentication.models import User
from rest_framework.response import Response
from rest_framework import status
from konkurs.serializers import ChildrenSerializer
from .serializers import (
    ChildSerializer,
    ChildWorkSerializer,
)
from .models import Child
from rest_framework.parsers import MultiPartParser
from konkurs_admin.serializers import (
    ParticipantSerializer,
    RegisterParticipantSerializer
)
from konkurs.models import (
    ChildWork,
    Participant,
    Competition
)

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
        serializer = ChildrenSerializer(children, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The first name of the child.",
                    example="John"
                ),
                'last_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The last name of the child.",
                    example="Doe"
                ),
                'birth_date': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The birth date of the child.",
                    example="2015-06-15"
                ),
            },
            required=['first_name', 'last_name', 'birth_date'],
        ),
        responses={
            201: openapi.Response(
                description="Child registered successfully.",
                examples={
                    "application/json": {
                        "id": 1,
                        "first_name": "John",
                        "last_name": "Doe",
                        "birth_date": "2015-06-15",
                        "user": 123
                    }
                }
            ),
            400: openapi.Response(
                description="Invalid input data or registration limit reached.",
                examples={
                    "application/json": {
                        "message": "You have already registered 5 children"
                    }
                }
            ),
        },
        operation_summary="Create a child",
        operation_description=(
                "This endpoint allows a user to register a child. The user can only register up to 5 children. "
                "The child's first name, last name, and birth date are required fields."
        )
    )
    def create(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        try:
            user = User.objects.filter(phone_number=phone_number).first()
        except User.DoesNotExist:
            return Response({'message': 'User with this phone number does not exist.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if user.children_count >= 5:
            return Response({'message': 'You have already registered 5 children'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ChildSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            user.children_count += 1
            user.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The updated first name of the child.",
                    example="John"
                ),
                'last_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The updated last name of the child.",
                    example="Doe"
                ),
                'birth_date': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The updated birth date of the child.",
                    example="2015-06-15"
                ),
            },
            required=[],
        ),
        responses={
            200: openapi.Response(
                description="Child updated successfully.",
                examples={
                    "application/json": {
                        "id": 1,
                        "first_name": "John",
                        "last_name": "Doe",
                        "birth_date": "2015-06-15",
                        "user": 123
                    }
                }
            ),
            400: openapi.Response(
                description="Invalid input data.",
                examples={
                    "application/json": {
                        "first_name": ["This field is required."]
                    }
                }
            ),
            404: openapi.Response(
                description="Child not found.",
                examples={
                    "application/json": {
                        "error": "Child not found"
                    }
                }
            ),
        },
        operation_summary="Update child details",
        operation_description=(
                "This endpoint allows updating the details of a specific child. "
                "The child is identified by their ID (`pk`). Only the fields provided in the request will be updated."
        )
    )
    def update(self, request, pk, *args, **kwargs):
        child = Child.objects.filter(id=pk).first()
        if child is None:
            return Response({'error': 'Child not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ChildSerializer(child, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="Child details retrieved successfully.",
                examples={
                    "application/json": {
                        "id": 1,
                        "first_name": "John",
                        "last_name": "Doe",
                        "birth_date": "2015-06-15",
                        "user": 123
                    }
                }
            ),
            404: openapi.Response(
                description="Child not found.",
                examples={
                    "application/json": {
                        "error": "Child not found"
                    }
                }
            ),
        },
        operation_summary="Get child details by ID",
        operation_description=(
                "This endpoint retrieves the details of a specific child by their ID (`pk`). "
                "If the child is not found, a 404 error is returned."
        )
    )
    def get_by_id(self, request, pk, *args, **kwargs):
        child = Child.objects.filter(id=pk).first()
        if child is None:
            return Response({'error': 'Child not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ChildSerializer(child)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="List of children retrieved successfully.",
                examples={
                    "application/json": [
                        {
                            "id": 1,
                            "first_name": "John",
                            "last_name": "Doe",
                            "birth_date": "2015-06-15",
                            "user": 123
                        },
                        {
                            "id": 2,
                            "first_name": "Jane",
                            "last_name": "Smith",
                            "birth_date": "2017-08-25",
                            "user": 123
                        }
                    ]
                }
            ),
            401: openapi.Response(
                description="User not authenticated.",
                examples={
                    "application/json": {
                        "message": "User not authenticated"
                    }
                }
            ),
            404: openapi.Response(
                description="No children found for the user.",
                examples={
                    "application/json": {
                        "message": "You haven't added any children yet"
                    }
                }
            ),
        },
        operation_summary="Get a list of children for the authenticated user",
        operation_description=(
                "This endpoint retrieves a list of children that belong to the authenticated user. "
                "If the user is not authenticated, a 401 error is returned. "
                "If the user hasn't added any children yet, a 404 error is returned."
        )
    )
    def list(self, request, *args, **kwargs):
        phone_number = request.data['phone_number']
        if phone_number is None:
            return Response({'error': 'Phone_number is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({'message': 'User with this phone number does not exist.'},
                            status=status.HTTP_400_BAD_REQUEST)

        children = Child.objects.filter(user=user)
        if not children.exists():
            return Response({'message': "You haven't added any children yet"},
                            status=status.HTTP_404_NOT_FOUND)

        serializer = ChildSerializer(children, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="Child successfully deleted.",
                examples={
                    "application/json": {
                        "message": "Child successfully deleted"
                    }
                }
            ),
            401: openapi.Response(
                description="User not authenticated.",
                examples={
                    "application/json": {
                        "message": "User not authenticated"
                    }
                }
            ),
            403: openapi.Response(
                description="Permission denied to delete the child.",
                examples={
                    "application/json": {
                        "message": "You do not have permission to delete this child"
                    }
                }
            ),
            404: openapi.Response(
                description="Child not found or user hasn't added any children.",
                examples={
                    "application/json": {
                        "message": "You have not added any children yet"
                    },
                    "application/json": {
                        "error": "Child not found"
                    }
                }
            ),
        },
        operation_summary="Delete a child record",
        operation_description=(
                "This endpoint allows the authenticated user to delete a child record. "
                "If the user is not authenticated, a 401 error is returned. "
                "If the user doesn't have any children, a 404 error is returned. "
                "If the child does not belong to the authenticated user, a 403 error is returned."
        )
    )
    def delete(self, request, pk, *args, **kwargs):
        user = request.user if request.user.is_authenticated else None

        if not user:
            phone_number = request.data.get('phone_number')
            if not phone_number:
                return Response({'message': 'Phone number is required.'}, status=status.HTTP_400_BAD_REQUEST)
            user = User.objects.filter(phone_number=phone_number).first()
            if not user:
                return Response({'message': 'User not found.'}, status=status.HTTP_400_BAD_REQUEST)

        if user.children_count == 0:
            return Response({'message': 'No children found to delete.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            child = Child.objects.get(id=pk, user=user)
        except Child.DoesNotExist:
            return Response({'message': 'Child not found or does not belong to you.'}, status=status.HTTP_404_NOT_FOUND)

        child.delete()
        user.children_count -= 1
        user.save()

        return Response({'message': 'Child successfully deleted.'}, status=status.HTTP_200_OK)


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
        serializer = RegisterParticipantSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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
            return Response(data={'error': 'Participant not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ChildWorkSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        files = request.FILES.getlist('files')
        ChildWork.objects.bulk_create([
            ChildWork(participant=participant, competition=participant.competition, files=file)
            for file in files
        ])
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)
