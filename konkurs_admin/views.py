from django.db import transaction
from django.db.models import Q
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from konkurs.models import (
    Competition,
    Participant,
    Category,
)
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from .models import Notification, Winner
from authentication.models import User
from .serializers import (
    CategorySerializer,
    GetCompetitionSerializer,
    ParticipantSerializer,
    JurySerializer,
    WinnerSerializer,
    ActiveParticipantSerializer,
    WinnerListSerializer,
    GetJurySerializer,
    GetCompetitionByIdSerializer,
    CreateCompetitionSerializer
)
from .pagination import CustomPagination


class CategoryViewSet(ViewSet):
    pagination_class = CustomPagination

    @swagger_auto_schema(
        operation_description="Get all Categories",
        operation_summary="Get all Categories",
        manual_parameters=[
            openapi.Parameter(
                'page', openapi.IN_QUERY,
                description="Page number (e.g., ?page=1)",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size', openapi.IN_QUERY,
                description="Number of items per page (e.g., ?page_size=10)",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total competitions'),
                    'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total pages available'),
                    'current_page': openapi.Schema(type=openapi.TYPE_INTEGER, description='Current page number'),
                    'page_size': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of items per page'),
                    'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description='Next page URL'),
                    'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True,
                                               description='Previous page URL'),
                    'results': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT))
                }
            ),
        },
        tags=['admin']
    )
    def get(self, request, *args, **kwargs):
        data = request.GET
        page = data.get('page')
        size = data.get('page_size')
        if not page or not size:
            return Response(data={'error': 'Size or Page is needed'}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': 'page must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': 'page size must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        categories = Category.objects.all()
        paginator = self.pagination_class()
        paginated_categories = paginator.paginate_queryset(categories, request)
        serializer = CategorySerializer(paginated_categories, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get Category By Id",
        operation_summary="Get Category By Id",
        responses={
            200: CategorySerializer(),
        },
        tags=['admin']
    )
    def get_by_id(self, request, *args, **kwargs):
        category = Category.objects.filter(id=kwargs['pk']).first()
        if category is None:
            return Response(data={'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(category)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Create Category",
        operation_summary="Create Category",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='name'),
            },
            required=['name']
        ),
        responses={201: CategorySerializer()},
        tags=['admin'],
    )
    def create(self, request, *args, **kwargs):
        serializer = CategorySerializer(data=request.data)

        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Update Category",
        operation_summary="Update Category",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='name'),
            },
            required=[]
        ),
        responses={200: CategorySerializer()},
        tags=['admin'],
    )
    def update(self, request, *args, **kwargs):
        competition = Category.objects.filter(id=kwargs['pk']).first()
        if competition is None:
            return Response(data={'error': 'Competition not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(competition, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data={'updated': serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Delete Category",
        operation_summary="Delete Category",
        responses={
            200: 'Successfully Deleted',
        },
        tags=['admin']
    )
    def delete(self, request, *args, **kwargs):
        competition = Category.objects.filter(id=kwargs['pk']).first()
        if competition is None:
            return Response(data={'error': 'Competition not found'}, status=status.HTTP_404_NOT_FOUND)
        competition.delete()
        return Response(data={'message': 'Successfully deleted'}, status=status.HTTP_200_OK)


class CompetitionViewSet(ViewSet):
    pagination_class = CustomPagination
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Get Competitions",
        operation_summary="Get Competitions",
        manual_parameters=[
            openapi.Parameter(
                'page', openapi.IN_QUERY,
                description="Page number (e.g., ?page=1)",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size', openapi.IN_QUERY,
                description="Number of items per page (e.g., ?page_size=10)",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total competitions'),
                    'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total pages available'),
                    'current_page': openapi.Schema(type=openapi.TYPE_INTEGER, description='Current page number'),
                    'page_size': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of items per page'),
                    'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description='Next page URL'),
                    'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True,
                                               description='Previous page URL'),
                    'results': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT))
                }
            ),
        },
        tags=['admin']
    )
    def get_comp(self, request, *args, **kwargs):
        data = request.GET
        page = data.get('page')
        size = data.get('page_size')
        if not page or not size:
            return Response(data={'error': 'Size or Page is needed'}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': 'page must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': 'page size must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        competitions = Competition.objects.all()
        paginator = self.pagination_class()
        paginated_competitions = paginator.paginate_queryset(competitions, request)
        serializer = GetCompetitionSerializer(paginated_competitions, many=True)
        return paginator.get_paginated_response(serializer.data)
        # return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Search Competition",
        operation_summary="Search Competition",
        manual_parameters=[
            openapi.Parameter(
                'search', type=openapi.TYPE_STRING, description='search_competition', in_=openapi.IN_QUERY
            ),
            openapi.Parameter(
                'page', openapi.IN_QUERY,
                description="Page number (e.g., ?page=1)",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size', openapi.IN_QUERY,
                description="Number of items per page (e.g., ?page_size=10)",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total competitions'),
                    'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total pages available'),
                    'current_page': openapi.Schema(type=openapi.TYPE_INTEGER, description='Current page number'),
                    'page_size': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of items per page'),
                    'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description='Next page URL'),
                    'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True,
                                               description='Previous page URL'),
                    'results': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT))
                }
            ),
        },
        tags=['admin'],
    )
    def search_comp(self, request, *args, **kwargs):
        data = request.GET
        page = data.get('page')
        size = data.get('page_size')
        if not page or not size:
            return Response(data={'error': 'Size or Page is needed'}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': 'page must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': 'page size must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        search = request.GET.get('search', '')
        comp = Competition.objects.filter(name__icontains=search)
        paginator = self.pagination_class()
        paginated_competitions = paginator.paginate_queryset(comp, request)
        serializer = GetCompetitionSerializer(paginated_competitions, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_description="Filter Comp by Category",
        operation_summary="Filter Comp by Category",
        manual_parameters=[
            openapi.Parameter(
                'category', type=openapi.TYPE_INTEGER, description='filter_comp_by_category', in_=openapi.IN_QUERY
            ),
            openapi.Parameter(
                'page', openapi.IN_QUERY,
                description="Page number (e.g., ?page=1)",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size', openapi.IN_QUERY,
                description="Number of items per page (e.g., ?page_size=10)",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total competitions'),
                    'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total pages available'),
                    'current_page': openapi.Schema(type=openapi.TYPE_INTEGER, description='Current page number'),
                    'page_size': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of items per page'),
                    'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description='Next page URL'),
                    'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True,
                                               description='Previous page URL'),
                    'results': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT))
                }
            ),
        },
        tags=['admin'],
    )
    def filter_comp(self, request, *args, **kwargs):
        data = request.GET
        category = data.get('category')
        page = data.get('page')
        size = data.get('page_size')
        if not page or not size:
            return Response(data={'error': 'Size or Page is needed'}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': 'page must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': 'page size must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        cat = Category.objects.filter(id=category).first()
        if cat is None:
            return Response(data={'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
        competitions = Competition.objects.all()
        if category:
            competitions = Competition.objects.filter(category=category)
        paginator = self.pagination_class()
        paginated_competitions = paginator.paginate_queryset(competitions, request)
        serializer = GetCompetitionSerializer(paginated_competitions, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get Competition By Id",
        operation_summary="Get Competition By Id",
        responses={
            200: GetCompetitionByIdSerializer(),
        },
        tags=['admin']
    )
    def get_comp_by_id(self, request, *args, **kwargs):
        competition = Competition.objects.filter(id=kwargs['pk']).first()
        if competition is None:
            return Response(data={'error': 'Competition not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = GetCompetitionByIdSerializer(competition)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Search Participants for finished comp",
        operation_summary="Search Participants for finished comp",
        manual_parameters=[
            openapi.Parameter(
                'search', type=openapi.TYPE_STRING, description='search_participants', in_=openapi.IN_QUERY
            ),
            openapi.Parameter(
                'page', openapi.IN_QUERY,
                description="Page number (e.g., ?page=1)",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size', openapi.IN_QUERY,
                description="Number of items per page (e.g., ?page_size=10)",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total participants'),
                    'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total pages available'),
                    'current_page': openapi.Schema(type=openapi.TYPE_INTEGER, description='Current page number'),
                    'page_size': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of items per page'),
                    'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description='Next page URL'),
                    'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True,
                                               description='Previous page URL'),
                    'results': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT))
                }
            ),
        },
        tags=['admin'],
    )
    def search_participant(self, request, *args, **kwargs):
        data = request.GET
        page = data.get('page')
        size = data.get('page_size')
        if not page or not size:
            return Response(data={'error': 'Size or Page is needed'}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': 'page must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': 'page size must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        search = request.GET.get('search', '')
        comp = Competition.objects.filter(id=kwargs['pk']).first()
        if comp is None:
            return Response(data={'error': 'Competition not found'}, status=status.HTTP_200_OK)
        if comp.status != 2:
            return Response(data={'error': 'This comp is not finished'}, status=status.HTTP_400_BAD_REQUEST)
        participant = Participant.objects.filter(competition=comp)
        participant = participant.filter(
            Q(child__first_name__icontains=search) |
            Q(child__last_name__icontains=search) |
            Q(child__middle_name__icontains=search)
        )
        paginator = self.pagination_class()
        paginated_participant = paginator.paginate_queryset(participant, request)
        serializer = ActiveParticipantSerializer(paginated_participant, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get Participants for finished comp",
        operation_summary="Get Participants for finished comp",
        manual_parameters=[
            openapi.Parameter(
                'page', openapi.IN_QUERY,
                description="Page number (e.g., ?page=1)",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size', openapi.IN_QUERY,
                description="Number of items per page (e.g., ?page_size=10)",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total participants'),
                    'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total pages available'),
                    'current_page': openapi.Schema(type=openapi.TYPE_INTEGER, description='Current page number'),
                    'page_size': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of items per page'),
                    'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description='Next page URL'),
                    'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True,
                                               description='Previous page URL'),
                    'results': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT))
                }
            ),
        },
        tags=['admin']
    )
    def participants(self, request, *args, **kwargs):
        data = request.GET
        page = data.get('page')
        size = data.get('page_size')
        if not page or not size:
            return Response(data={'error': 'Size or Page is needed'}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': 'page must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': 'page size must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        comp = Competition.objects.filter(id=kwargs['pk']).first()
        if comp is None:
            return Response(data={'error': 'Competition not found'}, status=status.HTTP_400_BAD_REQUEST)
        if comp.status != 2:
            return Response(data={'error': 'This comp is not finished'}, status=status.HTTP_400_BAD_REQUEST)
        participants = Participant.objects.filter(competition=comp, marked_status=2, action=2)
        paginator = self.pagination_class()
        paginated_participants = paginator.paginate_queryset(participants, request)
        serializer = ActiveParticipantSerializer(paginated_participants, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_description="Search Winners for finished comp",
        operation_summary="Search Winners for finished comp",
        manual_parameters=[
            openapi.Parameter(
                'search', type=openapi.TYPE_STRING, description='search_winners', in_=openapi.IN_QUERY
            ),
            openapi.Parameter(
                'page', openapi.IN_QUERY,
                description="Page number (e.g., ?page=1)",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size', openapi.IN_QUERY,
                description="Number of items per page (e.g., ?page_size=10)",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total winners'),
                    'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total pages available'),
                    'current_page': openapi.Schema(type=openapi.TYPE_INTEGER, description='Current page number'),
                    'page_size': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of items per page'),
                    'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description='Next page URL'),
                    'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True,
                                               description='Previous page URL'),
                    'results': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT))
                }
            ),
        },
        tags=['admin'],
    )
    def search_winners(self, request, *args, **kwargs):
        data = request.GET
        page = data.get('page')
        size = data.get('page_size')
        if not page or not size:
            return Response(data={'error': 'Size or Page is needed'}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': 'page must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': 'page size must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        search = request.GET.get('search', '')
        comp = Competition.objects.filter(id=kwargs['pk']).first()
        if comp is None:
            return Response(data={'error': 'Competition not found'}, status=status.HTTP_200_OK)
        if comp.status != 2:
            return Response(data={'error': 'This com is not finished'}, status=status.HTTP_400_BAD_REQUEST)
        winners = Winner.objects.filter(competition=comp)
        winners = winners.filter(
            Q(participant__child__first_name__icontains=search) |
            Q(participant__child__last_name__icontains=search) |
            Q(participant__child__middle_name__icontains=search)
        )
        paginator = self.pagination_class()
        paginated_winners = paginator.paginate_queryset(winners, request)
        serializer = WinnerListSerializer(paginated_winners, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get Winners for finished comp",
        operation_summary="Get Winners for finished comp",
        manual_parameters=[
            openapi.Parameter(
                'page', openapi.IN_QUERY,
                description="Page number (e.g., ?page=1)",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size', openapi.IN_QUERY,
                description="Number of items per page (e.g., ?page_size=10)",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total winners'),
                    'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total pages available'),
                    'current_page': openapi.Schema(type=openapi.TYPE_INTEGER, description='Current page number'),
                    'page_size': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of items per page'),
                    'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description='Next page URL'),
                    'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True,
                                               description='Previous page URL'),
                    'results': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT))
                }
            ),
        },
        tags=['admin']
    )
    def winners(self, request, *args, **kwargs):
        data = request.GET
        page = data.get('page')
        size = data.get('page_size')
        if not page or not size:
            return Response(data={'error': 'Size or Page is needed'}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': 'page must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': 'page size must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        comp = Competition.objects.filter(id=kwargs['pk']).first()
        if comp is None:
            return Response(data={'error': 'Competition not found'}, status=status.HTTP_404_NOT_FOUND)
        if comp.status != 2:
            return Response(data={'error': 'This comp is not finished'}, status=status.HTTP_400_BAD_REQUEST)
        winners = Winner.objects.filter(competition=comp).order_by('place')
        paginator = self.pagination_class()
        paginated_winners = paginator.paginate_queryset(winners, request)
        serializer = WinnerListSerializer(paginated_winners, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_description="Create comp",
        operation_summary="Create comp",
        manual_parameters=[
            openapi.Parameter(
                name='image',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="image"
            ),
            openapi.Parameter(
                name='name',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="name",
            ), openapi.Parameter(
                name='category',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_INTEGER,
                required=True,
                description="category",
            ), openapi.Parameter(
                name='description',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="description",
            ), openapi.Parameter(
                name='comp_start_date',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="comp_start_date",
            ), openapi.Parameter(
                name='comp_start_time',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="comp_start_time",
            ), openapi.Parameter(
                name='comp_end_date',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="comp_end_date",
            ), openapi.Parameter(
                name='comp_end_time',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="comp_end_time",
            ), openapi.Parameter(
                name='application_start_date',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="application_start_date",
            ), openapi.Parameter(
                name='application_start_time',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="application_start_time",
            ), openapi.Parameter(
                name='application_end_date',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="application_end_date",
            ), openapi.Parameter(
                name='application_end_time',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="application_end_time",
            ), openapi.Parameter(
                name='rules',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="rules",
            ),
        ],
        responses={201: CreateCompetitionSerializer()},
        tags=['admin'],
    )
    def create_comp(self, request, *args, **kwargs):
        serializer = CreateCompetitionSerializer(data=request.data)
        # serializer = CompetitionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        # comp = serializer.save()
        # criteria = request.data.get('criteria', [])
        # for criteria_name in criteria:
        #     GradeCriteria.objects.create(competition=comp, criteria=criteria_name)
        # updated_serializer = CompetitionSerializer(comp)
        # return Response(data=updated_serializer.data, status=status.HTTP_201_CREATED)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Update comp",
        operation_summary="Update comp",
        manual_parameters=[
            openapi.Parameter(
                name='image',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                description="image"
            ),
            openapi.Parameter(
                name='name',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description="name",
            ), openapi.Parameter(
                name='category',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_INTEGER,
                description="category",
            ), openapi.Parameter(
                name='description',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description="description",
            ), openapi.Parameter(
                name='comp_start_date',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description="comp_start_date",
            ), openapi.Parameter(
                name='comp_start_time',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description="comp_start_time",
            ), openapi.Parameter(
                name='comp_end_date',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description="comp_end_date",
            ), openapi.Parameter(
                name='comp_end_time',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description="comp_end_time",
            ), openapi.Parameter(
                name='application_start_date',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description="application_start_date",
            ), openapi.Parameter(
                name='application_start_time',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description="application_start_time",
            ), openapi.Parameter(
                name='application_end_date',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description="application_end_date",
            ), openapi.Parameter(
                name='application_end_time',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description="application_end_time",
            ), openapi.Parameter(
                name='rules',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description="rules",
            ),
        ],
        responses={201: CreateCompetitionSerializer()},
        tags=['admin'],
    )
    def update_comp(self, request, *args, **kwargs):  # not finished
        comp = Competition.objects.filter(id=kwargs['pk']).first()
        if comp is None:
            return Response(data={'error': 'Comp is not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CreateCompetitionSerializer(comp, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data={'updated': serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Delete Competition",
        operation_summary="Delete Competition",
        responses={
            200: 'Successfully Deleted'
        },
        tags=['admin']
    )
    def delete_comp(self, request, *args, **kwargs):  # not finished
        competition = Competition.objects.filter(id=kwargs['pk']).first()
        if competition is None:
            return Response(data={'error': 'Competition not found'}, status=status.HTTP_404_NOT_FOUND)
        competition.delete()
        return Response(data={'message': 'Competition successfully deleted'}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get Participants Requests for active comp",
        operation_summary="Get Participants Requests for active comp",
        manual_parameters=[
            openapi.Parameter(
                'page', openapi.IN_QUERY,
                description="Page number (e.g., ?page=1)",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size', openapi.IN_QUERY,
                description="Number of items per page (e.g., ?page_size=10)",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total participants requests'),
                    'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total pages available'),
                    'current_page': openapi.Schema(type=openapi.TYPE_INTEGER, description='Current page number'),
                    'page_size': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of items per page'),
                    'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description='Next page URL'),
                    'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True,
                                               description='Previous page URL'),
                    'results': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT))
                }
            ),
        },
        tags=['admin']
    )
    def participants_requests(self, request, *args, **kwargs):
        data = request.GET
        page = data.get('page')
        size = data.get('page_size')
        if not page or not size:
            return Response(data={'error': 'Size or Page is needed'}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': 'page must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': 'page size must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        competition = Competition.objects.filter(id=kwargs['pk']).first()
        if competition is None:
            return Response(data={'error': 'Competition not found'}, status=status.HTTP_404_NOT_FOUND)
        if competition.status != 1:
            return Response(data={'error': 'Comp is not active'}, status=status.HTTP_400_BAD_REQUEST)
        participants = Participant.objects.filter(competition=competition, action=1)
        paginator = self.pagination_class()
        paginated_participants = paginator.paginate_queryset(participants, request)
        serializer = ParticipantSerializer(paginated_participants, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_description="Approve request for active comp",
        operation_summary="Approve request for active comp",
        manual_parameters=[
            openapi.Parameter(
                name='participant',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_INTEGER,
                description='Participant ID',
                required=False
            ),
            openapi.Parameter(
                name='action',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description='Action to perform: "accept" or "decline"',
                enum=['accept', 'decline'],
                required=True
            ),
        ],
        responses={200: 'Ok'},
        tags=['admin'],
    )
    def approve(self, request, *args, **kwargs):
        action = request.data['action']
        comp = Competition.objects.filter(id=kwargs['pk']).first()
        if comp is None:
            return Response(data={'error': 'Comp is not found'}, status=status.HTTP_404_NOT_FOUND)
        if comp.status != 1:
            return Response(data={'error': 'Comp is not active'}, status=status.HTTP_400_BAD_REQUEST)
        participant = Participant.objects.filter(id=request.data['participant']).first()
        if participant is None:
            return Response(data={'error': 'Participant not found'}, status=status.HTTP_404_NOT_FOUND)

        if action == 'accept':
            participant.action = 2
        elif action == 'decline':
            message = (
                f'Dear {participant.child.first_name}, '
                f'You have an error to fill register or work for the {participant.competition.name}'
            )
            participant.action = 3
            Notification.objects.create(user=participant.child.user, child=participant.child,
                                        competition=participant.competition, message=message)
        else:
            return Response(data={'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
        participant.save()
        return Response(data={'message': f'Request {action}'}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get Active Participants for active comp",
        operation_summary="Get Active Participants for active comp",
        manual_parameters=[
            openapi.Parameter(
                'page', openapi.IN_QUERY,
                description="Page number (e.g., ?page=1)",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size', openapi.IN_QUERY,
                description="Number of items per page (e.g., ?page_size=10)",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total active participants'),
                    'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total pages available'),
                    'current_page': openapi.Schema(type=openapi.TYPE_INTEGER, description='Current page number'),
                    'page_size': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of items per page'),
                    'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description='Next page URL'),
                    'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True,
                                               description='Previous page URL'),
                    'results': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT))
                }
            ),
        },
        tags=['admin']
    )
    def active_participants(self, request, *args, **kwargs):
        data = request.GET
        page = data.get('page')
        size = data.get('page_size')
        if not page or not size:
            return Response(data={'error': 'Size or Page is needed'}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': 'page must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': 'page size must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        comp = Competition.objects.filter(id=kwargs['pk']).first()
        if comp is None:
            return Response(data={'error': 'Competition not found'}, status=status.HTTP_400_BAD_REQUEST)
        if comp.status != 1:
            return Response(data={'error': 'Comp is not active'}, status=status.HTTP_400_BAD_REQUEST)
        participants = Participant.objects.filter(competition=comp, marked_status=2)
        paginator = self.pagination_class()
        paginated_participants = paginator.paginate_queryset(participants, request)
        serializer = ActiveParticipantSerializer(paginated_participants, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_description="Create Winners for active comp",
        operation_summary="Create Winners for active comp",
        manual_parameters=[
            openapi.Parameter(
                name='place',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_INTEGER,
                required=True,
                description="place"
            ),
            openapi.Parameter(
                name='first_name',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="first_name",
            ), openapi.Parameter(
                name='last_name',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="last_name",
            ), openapi.Parameter(
                name='birth_date',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="birth_date",
            ), openapi.Parameter(
                name='email',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="email",
            ), openapi.Parameter(
                name='phone_number',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="phone_number",
            ), openapi.Parameter(
                name='grade',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_INTEGER,
                required=True,
                description="grade",
            ), openapi.Parameter(
                name='jury_comment',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="jury_comment",
            ), openapi.Parameter(
                name='certificate',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="certificate",
            ), openapi.Parameter(
                name='address_for_physical_certificate',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="address_for_physical_certificate",
            ),
        ],
        responses={201: WinnerSerializer()},
        tags=['admin'],
    )
    def create_winners(self, request, *args, **kwargs):  # not finished
        comp = Competition.objects.filter(id=kwargs['pk']).first()
        if comp is None:
            return Response(data={'error': 'Competition not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = WinnerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        participant = Participant.objects.filter(competition=comp,
                                                 child__first_name=request.data['first_name'],
                                                 child__last_name=request.data['last_name']).first()
        if participant is None:
            return Response(data={'error': 'Participant not found'}, status=status.HTTP_404_NOT_FOUND)
        participant.winner = True
        participant.save()
        serializer.validated_data['competition'] = comp
        serializer.validated_data['participant'] = participant
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Get Others for active comp",
        operation_summary="Get Others for active comp",
        manual_parameters=[
            openapi.Parameter(
                'page', openapi.IN_QUERY,
                description="Page number (e.g., ?page=1)",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size', openapi.IN_QUERY,
                description="Number of items per page (e.g., ?page_size=10)",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total other participants'),
                    'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total pages available'),
                    'current_page': openapi.Schema(type=openapi.TYPE_INTEGER, description='Current page number'),
                    'page_size': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of items per page'),
                    'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description='Next page URL'),
                    'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True,
                                               description='Previous page URL'),
                    'results': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT))
                }
            ),
        },
        tags=['admin']
    )
    def others(self, request, *args, **kwargs):
        data = request.GET
        page = data.get('page')
        size = data.get('page_size')
        if not page or not size:
            return Response(data={'error': 'Size or Page is needed'}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': 'page must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': 'page size must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        comp = Competition.objects.filter(id=kwargs['pk']).first()
        if comp is None:
            return Response(data={'error': 'Competition not found'}, status=status.HTTP_400_BAD_REQUEST)
        if comp.status != 1:
            return Response(data={'error': 'Comp is not active'}, status=status.HTTP_400_BAD_REQUEST)
        participants = Participant.objects.filter(competition=comp, winner=False)
        paginator = self.pagination_class()
        paginated_participants = paginator.paginate_queryset(participants, request)
        serializer = ActiveParticipantSerializer(paginated_participants, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_description="Send thank you message for active comp",
        operation_summary="Send thank you message for active comp",
        manual_parameters=[
            openapi.Parameter(
                name='message',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description='Message to send to participants',
                required=True
            )
        ],
        responses={200: 'Thank you message sent to all participants'},
        tags=['admin'],
    )
    def send_thank_you_message(self, request, *args, **kwargs):
        competition_id = kwargs.get('pk')
        message_text = request.data.get('message')
        comp = Competition.objects.filter(id=competition_id).first()
        if comp is None:
            return Response(data={'error': 'Competition not found'}, status=status.HTTP_404_NOT_FOUND)
        if not message_text:
            return Response(data={"error": "Message cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

        participants = Participant.objects.filter(
            competition_id=competition_id, winner=False
        ).select_related('child__user')

        notifications = [
            Notification(user=participant.child.user, child=participant.child, message=message_text, competition=comp)
            for participant in participants if participant.child and participant.child.user
        ]

        if not notifications:
            return Response(data={'error': 'It has no any other participants to send notification'},
                            status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            Notification.objects.bulk_create(notifications)

        return Response({"success": "Thank you message sent to all participants"}, status=status.HTTP_201_CREATED)


class JuryViewSet(ViewSet):
    pagination_class = CustomPagination

    @swagger_auto_schema(
        operation_description="Get all juries",
        operation_summary="Get all juries",
        manual_parameters=[
            openapi.Parameter(
                'page', openapi.IN_QUERY,
                description="Page number (e.g., ?page=1)",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size', openapi.IN_QUERY,
                description="Number of items per page (e.g., ?page_size=10)",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total juries'),
                    'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total pages available'),
                    'current_page': openapi.Schema(type=openapi.TYPE_INTEGER, description='Current page number'),
                    'page_size': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of items per page'),
                    'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description='Next page URL'),
                    'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True,
                                               description='Previous page URL'),
                    'results': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT))
                }
            ),
        },
        tags=['admin']
    )
    def get_all(self, request, *args, **kwargs):
        data = request.GET
        page = data.get('page')
        size = data.get('page_size')
        if not page or not size:
            return Response(data={'error': 'Size or Page is needed'}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': 'page must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': 'page size must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        juries = User.objects.filter(role=2)
        paginator = self.pagination_class()
        paginated_juries = paginator.paginate_queryset(juries, request)
        serializer = GetJurySerializer(paginated_juries, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_description="Search Juries",
        operation_summary="Search Juries",
        manual_parameters=[
            openapi.Parameter(
                'search', type=openapi.TYPE_STRING, description='search_juries', in_=openapi.IN_QUERY
            ),
            openapi.Parameter(
                'page', openapi.IN_QUERY,
                description="Page number (e.g., ?page=1)",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size', openapi.IN_QUERY,
                description="Number of items per page (e.g., ?page_size=10)",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total juries'),
                    'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total pages available'),
                    'current_page': openapi.Schema(type=openapi.TYPE_INTEGER, description='Current page number'),
                    'page_size': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of items per page'),
                    'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description='Next page URL'),
                    'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True,
                                               description='Previous page URL'),
                    'results': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT))
                }
            ),
        },
        tags=['admin'],
    )
    def search_juries(self, request, *args, **kwargs):
        data = request.GET
        page = data.get('page')
        size = data.get('page_size')
        if not page or not size:
            return Response(data={'error': 'Size or Page is needed'}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': 'page must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': 'page size must be greater than 0 or must be integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        search = request.GET.get('search', '')
        juries = User.objects.filter(role=2)
        juries = juries.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(middle_name__icontains=search)
        )
        paginator = self.pagination_class()
        paginated_juries = paginator.paginate_queryset(juries, request)
        serializer = GetJurySerializer(paginated_juries, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get Jury By Id",
        operation_summary="Get Jury By Id",
        responses={
            200: JurySerializer(),
        },
        tags=['admin']
    )
    def get_by_id(self, request, *args, **kwargs):
        jury = User.objects.filter(id=kwargs['pk'], role=2).first()
        if jury is None:
            return Response(data={'error': 'Jury not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = GetJurySerializer(jury)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Create Jury",
        operation_summary="Create Jury",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='first_name'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='last_name'),
                'middle_name': openapi.Schema(type=openapi.TYPE_STRING, description='middle_name'),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='phone_number'),
                'birth_date': openapi.Schema(type=openapi.TYPE_STRING, description='birth_date'),
                'place_of_work': openapi.Schema(type=openapi.TYPE_STRING, description='place_of_work'),
                'academic_degree': openapi.Schema(type=openapi.TYPE_INTEGER, description='academic_degree'),
                'speciality': openapi.Schema(type=openapi.TYPE_STRING, description='speciality'),
                'category': openapi.Schema(type=openapi.TYPE_INTEGER, description='category'),
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='username'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='password'),
                'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, description='confirm_password'),
            },
            required=['first_name', 'last_name', 'middle_name', 'birth_date', 'place_of_work', 'phone_number',
                      'academic_degree', 'speciality', 'category', 'username', 'password', 'confirm_password']
        ),
        responses={201: JurySerializer()},
        tags=['admin'],
    )
    def create(self, request, *args, **kwargs):
        serializer = JurySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.validated_data['role'] = 2
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Update Jury",
        operation_summary="Update Jury",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='first_name'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='last_name'),
                'middle_name': openapi.Schema(type=openapi.TYPE_INTEGER, description='middle_name'),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='phone_number'),
                'birth_date': openapi.Schema(type=openapi.TYPE_STRING, description='birth_date'),
                'place_of_work': openapi.Schema(type=openapi.TYPE_STRING, description='place_of_work'),
                'academic_degree': openapi.Schema(type=openapi.TYPE_INTEGER, description='academic_degree'),
                'speciality': openapi.Schema(type=openapi.TYPE_STRING, description='speciality'),
                'category': openapi.Schema(type=openapi.TYPE_INTEGER, description='category'),
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='username'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='password'),
                'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, description='confirm_password'),
            },
            required=[]
        ),
        responses={200: JurySerializer()},
        tags=['admin'],
    )
    def update(self, request, *args, **kwargs):
        jury = User.objects.filter(id=kwargs['pk'], role=2).first()
        if jury is None:
            return Response(data={'error': 'Jury not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = JurySerializer(jury, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data={'updated': serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Delete Jury",
        operation_summary="Delete Jury",
        responses={
            200: 'Successfully Deleted'
        },
        tags=['admin']
    )
    def delete(self, request, *args, **kwargs):
        jury = User.objects.filter(id=kwargs['pk'], role=2).first()
        if jury is None:
            return Response(data={'error': 'Jury not found'}, status=status.HTTP_404_NOT_FOUND)
        jury.delete()
        return Response(data={'message': 'Jury successfully deleted'}, status=status.HTTP_200_OK)
