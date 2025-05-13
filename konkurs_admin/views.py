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
from .models import (
    Notification,
    Winner,
    SocialMedia,
    ContactInformation,
    AboutResult,
    Policy,
    ResultImage,
    AboutUs,
)
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
    CreateCompetitionSerializer,
    #
    WebSocialMediaSerializer,
    ContactInformationSerializer,
    SpecialContactInformationSerializer,
    AboutResultSerializer,
    SpecialAboutResultSerializer,
    AboutUsSerializer,
    SpecialAboutUsSerializer,
    PolicySerializer,
    SpecialPolicySerializer, GetExistJurySerializer,
)
from konkurs.serializers import ResultImageSerializer, ContactUsSerializer
from konkurs.models import ContactUs
from .pagination import CustomPagination
from django.utils.translation import gettext as _


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
            return Response(data={'error': _('Size or Page is needed')}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': _('page must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': _('page size must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        categories = Category.objects.all()
        paginator = self.pagination_class()
        paginated_categories = paginator.paginate_queryset(categories, request)
        serializer = CategorySerializer(paginated_categories, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get all Categories for comp",
        operation_summary="Get all Categories for comp",
        responses={
            200: CategorySerializer(),
        },
        tags=['admin']
    )
    def get_all(self, request, *args, **kwargs):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

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
            return Response(data={'error': _('Category not found')}, status=status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(category, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Create Category",
        operation_summary="Create Category",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='name'),
                'name_uz': openapi.Schema(type=openapi.TYPE_STRING, description='name_uz'),
                'name_ru': openapi.Schema(type=openapi.TYPE_STRING, description='name_ru'),
                'name_en': openapi.Schema(type=openapi.TYPE_STRING, description='name_en'),
            },
            required=['name', 'name_uz', 'name_ru', 'name_en']
        ),
        responses={201: CategorySerializer()},
        tags=['admin'],
    )
    def create(self, request, *args, **kwargs):
        serializer = CategorySerializer(data=request.data, context={'request': request})

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Update Category",
        operation_summary="Update Category",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='name'),
                'name_uz': openapi.Schema(type=openapi.TYPE_STRING, description='name_uz'),
                'name_ru': openapi.Schema(type=openapi.TYPE_STRING, description='name_ru'),
                'name_en': openapi.Schema(type=openapi.TYPE_STRING, description='name_en'),
            },
            required=[]
        ),
        responses={200: CategorySerializer()},
        tags=['admin'],
    )
    def update(self, request, *args, **kwargs):
        competition = Category.objects.filter(id=kwargs['pk']).first()
        if competition is None:
            return Response(data={'error': _('Competition not found')}, status=status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(competition, data=request.data, partial=True, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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
            return Response(data={'error': _('Competition not found')}, status=status.HTTP_404_NOT_FOUND)
        competition.delete()
        return Response(data={'message': _('Successfully deleted')}, status=status.HTTP_200_OK)


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
            return Response(data={'error': _('Size or Page is needed')}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': _('page must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': _('page size must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        competitions = Competition.objects.all()
        paginator = self.pagination_class()
        paginated_competitions = paginator.paginate_queryset(competitions, request)
        serializer = GetCompetitionSerializer(paginated_competitions, many=True, context={'request': request})
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
            return Response(data={'error': _('Size or Page is needed')}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': _('page must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': _('page size must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        search = request.GET.get('search', '')
        comp = Competition.objects.filter(name__icontains=search)
        paginator = self.pagination_class()
        paginated_competitions = paginator.paginate_queryset(comp, request)
        serializer = GetCompetitionSerializer(paginated_competitions, many=True, context={'request': request})
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
            return Response(data={'error': _('Size or Page is needed')}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': _('page must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': _('page size must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        cat = Category.objects.filter(id=category).first()
        if cat is None:
            return Response(data={'error': _('Category not found')}, status=status.HTTP_404_NOT_FOUND)
        competitions = Competition.objects.all()
        if category:
            competitions = Competition.objects.filter(category=category)
        paginator = self.pagination_class()
        paginated_competitions = paginator.paginate_queryset(competitions, request)
        serializer = GetCompetitionSerializer(paginated_competitions, many=True, context={'request': request})
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
            return Response(data={'error': _('Competition not found')}, status=status.HTTP_404_NOT_FOUND)
        serializer = GetCompetitionByIdSerializer(competition, context={'request': request})
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
            return Response(data={'error': _('Size or Page is needed')}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': _('page must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': _('page size must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        search = request.GET.get('search', '')
        comp = Competition.objects.filter(id=kwargs['pk']).first()
        if comp is None:
            return Response(data={'error': _('Competition not found')}, status=status.HTTP_200_OK)
        if comp.status != 2:
            return Response(data={'error': _('This comp is not finished')}, status=status.HTTP_400_BAD_REQUEST)
        participant = Participant.objects.filter(competition=comp)
        participant = participant.filter(
            Q(child__first_name__icontains=search) |
            Q(child__last_name__icontains=search) |
            Q(child__middle_name__icontains=search)
        )
        paginator = self.pagination_class()
        paginated_participant = paginator.paginate_queryset(participant, request)
        serializer = ActiveParticipantSerializer(paginated_participant, many=True, context={'request': request})
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
            return Response(data={'error': _('Size or Page is needed')}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': _('page must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': _('page size must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        comp = Competition.objects.filter(id=kwargs['pk']).first()
        if comp is None:
            return Response(data={'error': _('Competition not found')}, status=status.HTTP_400_BAD_REQUEST)
        if comp.status != 2:
            return Response(data={'error': _('This comp is not finished')}, status=status.HTTP_400_BAD_REQUEST)
        participants = Participant.objects.filter(competition=comp, marked_status=2, action=2)
        paginator = self.pagination_class()
        paginated_participants = paginator.paginate_queryset(participants, request)
        serializer = ActiveParticipantSerializer(paginated_participants, many=True, context={'request': request})
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
            return Response(data={'error': _('Size or Page is needed')}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': _('page must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': _('page size must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        search = request.GET.get('search', '')
        comp = Competition.objects.filter(id=kwargs['pk']).first()
        if comp is None:
            return Response(data={'error': _('Competition not found')}, status=status.HTTP_200_OK)
        if comp.status != 2:
            return Response(data={'error': _('This com is not finished')}, status=status.HTTP_400_BAD_REQUEST)
        winners = Winner.objects.filter(competition=comp)
        winners = winners.filter(
            Q(participant__child__first_name__icontains=search) |
            Q(participant__child__last_name__icontains=search) |
            Q(participant__child__middle_name__icontains=search)
        )
        paginator = self.pagination_class()
        paginated_winners = paginator.paginate_queryset(winners, request)
        serializer = WinnerListSerializer(paginated_winners, many=True, context={'request': request})
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
            return Response(data={'error': _('Size or Page is needed')}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': _('page must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': _('page size must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        comp = Competition.objects.filter(id=kwargs['pk']).first()
        if comp is None:
            return Response(data={'error': _('Competition not found')}, status=status.HTTP_404_NOT_FOUND)
        if comp.status != 2:
            return Response(data={'error': _('This comp is not finished')}, status=status.HTTP_400_BAD_REQUEST)
        winners = Winner.objects.filter(competition=comp).order_by('place')
        paginator = self.pagination_class()
        paginated_winners = paginator.paginate_queryset(winners, request)
        serializer = WinnerListSerializer(paginated_winners, many=True, context={'request': request})
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
            ),
            openapi.Parameter(
                name='name_uz',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="name_uz",
            ),
            openapi.Parameter(
                name='name_ru',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="name_ru",
            ),
            openapi.Parameter(
                name='name_en',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="name_en",
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
                name='description_uz',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="description_uz",
            ), openapi.Parameter(
                name='description_ru',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="description_ru",
            ), openapi.Parameter(
                name='description_en',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="description_en",
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
        serializer = CreateCompetitionSerializer(data=request.data, context={'request': request})
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
            ),
            openapi.Parameter(
                name='name_uz',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description="name_uz",
            ),
            openapi.Parameter(
                name='name_ru',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description="name_ru",
            ),
            openapi.Parameter(
                name='name_en',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description="name_en",
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
                name='description_uz',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description="description_uz",
            ), openapi.Parameter(
                name='description_ru',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description="description_ru",
            ), openapi.Parameter(
                name='description_en',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description="description_en",
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
            ), openapi.Parameter(
                name='status',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_INTEGER,
                description="status",
            ),
        ],
        responses={200: CreateCompetitionSerializer()},
        tags=['admin'],
    )
    def update_comp(self, request, *args, **kwargs):  # not finished
        comp = Competition.objects.filter(id=kwargs['pk']).first()
        if comp is None:
            return Response(data={'error': _('Comp is not found')}, status=status.HTTP_404_NOT_FOUND)
        serializer = CreateCompetitionSerializer(comp, data=request.data, partial=True, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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
            return Response(data={'error': _('Competition not found')}, status=status.HTTP_404_NOT_FOUND)
        competition.delete()
        return Response(data={'message': _('Competition successfully deleted')}, status=status.HTTP_200_OK)

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
            return Response(data={'error': _('Size or Page is needed')}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': _('page must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': _('page size must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        competition = Competition.objects.filter(id=kwargs['pk']).first()
        if competition is None:
            return Response(data={'error': _('Competition not found')}, status=status.HTTP_404_NOT_FOUND)
        if competition.status != 1:
            return Response(data={'error': _('Comp is not active')}, status=status.HTTP_400_BAD_REQUEST)
        participants = Participant.objects.filter(competition=competition, action=1)
        paginator = self.pagination_class()
        paginated_participants = paginator.paginate_queryset(participants, request)
        serializer = ParticipantSerializer(paginated_participants, many=True, context={'request': request})
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
            return Response(data={'error': _('Comp is not found')}, status=status.HTTP_404_NOT_FOUND)
        if comp.status != 1:
            return Response(data={'error': _('Comp is not active')}, status=status.HTTP_400_BAD_REQUEST)
        participant = Participant.objects.filter(id=request.data['participant']).first()
        if participant is None:
            return Response(data={'error': _('Participant not found')}, status=status.HTTP_404_NOT_FOUND)

        if action == 'accept':
            participant.action = 2
        elif action == 'decline':
            message = (
                _("Dear %(participant_name)s.") % {'participant_name': participant.child.first_name},
                _("You have an error to fill register or work for the %(comp_name)s") % {
                    'comp_name': participant.competition.name}
            )
            participant.action = 3
            Notification.objects.create(user=participant.child.user, child=participant.child,
                                        competition=participant.competition, message=message)
        else:
            return Response(data={'error': _('Invalid action')}, status=status.HTTP_400_BAD_REQUEST)
        participant.save()
        return Response(data={'message': _("Request %(action)s") % {'action': action}}, status=status.HTTP_200_OK)

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
            return Response(data={'error': _('Size or Page is needed')}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': _('page must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': _('page size must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        comp = Competition.objects.filter(id=kwargs['pk']).first()
        if comp is None:
            return Response(data={'error': _('Competition not found')}, status=status.HTTP_400_BAD_REQUEST)
        if comp.status != 1:
            return Response(data={'error': _('Comp is not active')}, status=status.HTTP_400_BAD_REQUEST)
        participants = Participant.objects.filter(competition=comp, marked_status=2)
        paginator = self.pagination_class()
        paginated_participants = paginator.paginate_queryset(participants, request)
        serializer = ActiveParticipantSerializer(paginated_participants, many=True, context={'request': request})
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
            return Response(data={'error': _('Competition not found')}, status=status.HTTP_404_NOT_FOUND)
        serializer = WinnerSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        participant = Participant.objects.filter(competition=comp,
                                                 child__first_name=request.data['first_name'],
                                                 child__last_name=request.data['last_name']).first()
        if participant is None:
            return Response(data={'error': _('Participant not found')}, status=status.HTTP_404_NOT_FOUND)
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
            return Response(data={'error': _('Size or Page is needed')}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': _('page must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': _('page size must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        comp = Competition.objects.filter(id=kwargs['pk']).first()
        if comp is None:
            return Response(data={'error': _('Competition not found')}, status=status.HTTP_400_BAD_REQUEST)
        if comp.status != 1:
            return Response(data={'error': _('Comp is not active')}, status=status.HTTP_400_BAD_REQUEST)
        participants = Participant.objects.filter(competition=comp, winner=False)
        paginator = self.pagination_class()
        paginated_participants = paginator.paginate_queryset(participants, request)
        serializer = ActiveParticipantSerializer(paginated_participants, many=True, context={'request': request})
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
            return Response(data={'error': _('Competition not found')}, status=status.HTTP_404_NOT_FOUND)
        if not message_text:
            return Response(data={"error": _("Message cannot be empty")}, status=status.HTTP_400_BAD_REQUEST)

        participants = Participant.objects.filter(
            competition_id=competition_id, winner=False
        ).select_related('child__user')

        notifications = [
            Notification(user=participant.child.user, child=participant.child, message=message_text, competition=comp)
            for participant in participants if participant.child and participant.child.user
        ]

        if not notifications:
            return Response(data={'error': _('It has no any other participants to send notification')},
                            status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            Notification.objects.bulk_create(notifications)

        return Response({"success": _("Thank you message sent to all participants")}, status=status.HTTP_201_CREATED)


class JuryViewSet(ViewSet):
    pagination_class = CustomPagination
    parser_classes = [MultiPartParser, FormParser]

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
            return Response(data={'error': _('Size or Page is needed')}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': _('page must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': _('page size must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        juries = User.objects.filter(role=2)
        paginator = self.pagination_class()
        paginated_juries = paginator.paginate_queryset(juries, request)
        serializer = GetExistJurySerializer(paginated_juries, many=True, context={'request': request})
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
            return Response(data={'error': _('Size or Page is needed')}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': _('page must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': _('page size must be greater than 0 or must be integer')},
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
        serializer = GetJurySerializer(paginated_juries, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get Jury By Id",
        operation_summary="Get Jury By Id",
        responses={
            200: GetJurySerializer(),
        },
        tags=['admin']
    )
    def get_by_id(self, request, *args, **kwargs):
        jury = User.objects.filter(id=kwargs['pk'], role=2).first()
        if jury is None:
            return Response(data={'error': _('Jury not found')}, status=status.HTTP_404_NOT_FOUND)
        serializer = GetJurySerializer(jury, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Create Jury",
        operation_summary="Create Jury",
        manual_parameters=[
            openapi.Parameter(
                name='first_name',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="first_name"
            ),
            openapi.Parameter(
                name='last_name',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="last_name",
            ),
            openapi.Parameter(
                name='middle_name',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="middle_name",
            ),
            openapi.Parameter(
                name='phone_number',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="phone_number",
            ),
            openapi.Parameter(
                name='birth_date',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="birth_date",
            ),
            openapi.Parameter(
                name='place_of_work',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="place_of_work",
            ),
            openapi.Parameter(
                name='place_of_work_uz',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="place_of_work_uz",
            ),
            openapi.Parameter(
                name='place_of_work_ru',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="place_of_work_ru",
            ),
            openapi.Parameter(
                name='place_of_work_en',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="place_of_work_en",
            ),
            openapi.Parameter(
                name='academic_degree',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_INTEGER,
                required=True,
                description="academic_degree",
            ),
            openapi.Parameter(
                name='speciality',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="speciality",
            ),
            openapi.Parameter(
                name='speciality_uz',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="speciality_uz",
            ),
            openapi.Parameter(
                name='speciality_ru',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="speciality_ru",
            ),
            openapi.Parameter(
                name='speciality_en',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="speciality_en",
            ),
            openapi.Parameter(
                name='category',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_INTEGER,
                required=True,
                description="category",
            ),
            openapi.Parameter(
                name='username',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="username",
            ),
            openapi.Parameter(
                name='password',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="password",
            ),
            openapi.Parameter(
                name='confirm_password',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="confirm_password",
            ),
            openapi.Parameter(
                name='image',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="image",
            ),
            openapi.Parameter(
                name='email',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="email",
            ),
        ],
        responses={201: JurySerializer()},
        tags=['admin'],
    )
    def create(self, request, *args, **kwargs):
        serializer = JurySerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.validated_data['role'] = 2
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Get Exist Jury By Id for Update",
        operation_summary="Get Exist Jury By Id for Update",
        responses={
            200: GetExistJurySerializer(),
        },
        tags=['admin']
    )
    def get_exist_jury_by_id(self, request, *args, **kwargs):
        jury = User.objects.filter(id=kwargs['pk'], role=2).first()
        if jury is None:
            return Response(data={'error': _('Jury not found')}, status=status.HTTP_404_NOT_FOUND)
        serializer = GetExistJurySerializer(jury, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Update Jury",
        operation_summary="Update Jury",
        manual_parameters=[
            openapi.Parameter(
                name='first_name',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="first_name"
            ),
            openapi.Parameter(
                name='last_name',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="last_name",
            ),
            openapi.Parameter(
                name='middle_name',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="middle_name",
            ),
            openapi.Parameter(
                name='phone_number',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="phone_number",
            ),
            openapi.Parameter(
                name='birth_date',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="birth_date",
            ),
            openapi.Parameter(
                name='place_of_work',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="place_of_work",
            ),
            openapi.Parameter(
                name='place_of_work_uz',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="place_of_work_uz",
            ),
            openapi.Parameter(
                name='place_of_work_ru',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="place_of_work_ru",
            ),
            openapi.Parameter(
                name='place_of_work_en',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="place_of_work_en",
            ),
            openapi.Parameter(
                name='academic_degree',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_INTEGER,
                required=False,
                description="academic_degree",
            ),
            openapi.Parameter(
                name='speciality',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="speciality",
            ),
            openapi.Parameter(
                name='speciality_uz',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="speciality_uz",
            ),
            openapi.Parameter(
                name='speciality_ru',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="speciality_ru",
            ),
            openapi.Parameter(
                name='speciality_en',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="speciality_en",
            ),
            openapi.Parameter(
                name='category',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_INTEGER,
                required=False,
                description="category",
            ),
            openapi.Parameter(
                name='username',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="username",
            ),
            openapi.Parameter(
                name='password',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="password",
            ),
            openapi.Parameter(
                name='confirm_password',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="confirm_password",
            ),
            openapi.Parameter(
                name='image',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=False,
                description="image",
            ),
            openapi.Parameter(
                name='email',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="email",
            ),
        ],
        responses={200: JurySerializer()},
        tags=['admin'],
    )
    def update(self, request, *args, **kwargs):
        jury = User.objects.filter(id=kwargs['pk'], role=2).first()
        if jury is None:
            return Response(data={'error': _('Jury not found')}, status=status.HTTP_404_NOT_FOUND)
        serializer = JurySerializer(jury, data=request.data, partial=True, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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
            return Response(data={'error': _('Jury not found')}, status=status.HTTP_404_NOT_FOUND)
        jury.delete()
        return Response(data={'message': _('Jury successfully deleted')}, status=status.HTTP_200_OK)


class WebSocialMediaViewSet(ViewSet):
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Get Jury By Id",
        operation_summary="Get Jury By Id",
        responses={
            200: WebSocialMediaSerializer()
        },
        tags=['admin']
    )
    def get_by_id(self, request, *args, **kwargs):
        social_media = SocialMedia.objects.filter(id=kwargs['pk']).first()
        if social_media is None:
            return Response(data={'error': _('SocialMedia not found')}, status=status.HTTP_404_NOT_FOUND)
        serializer = WebSocialMediaSerializer(social_media, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get all Social Media",
        operation_summary="Get Social Media",
        responses={
            200: WebSocialMediaSerializer(),
        },
        tags=['admin']
    )
    def get_all(self, request, *args, **kwargs):
        social_media = SocialMedia.objects.all()
        serializer = WebSocialMediaSerializer(social_media, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Create Social Media",
        operation_summary="Create Social Media",
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
            ),
        ],
        responses={201: WebSocialMediaSerializer()},
        tags=['admin'],
    )
    def create(self, request, *args, **kwargs):
        serializer = WebSocialMediaSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Update Social Media",
        operation_summary="Update Social Media",
        manual_parameters=[
            openapi.Parameter(
                name='image',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=False,
                description="image"
            ),
            openapi.Parameter(
                name='name',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="name",
            ),
        ],
        responses={200: WebSocialMediaSerializer()},
        tags=['admin'],
    )
    def update(self, request, *args, **kwargs):
        social_media = SocialMedia.objects.filter(id=kwargs['pk']).first()
        if social_media is None:
            return Response(data={'error': _('SocialMedia not found')}, status=status.HTTP_404_NOT_FOUND)
        serializer = WebSocialMediaSerializer(social_media, data=request.data, partial=True,
                                              context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Delete Social Media",
        operation_summary="Delete Social Media",
        responses={
            200: 'Successfully Deleted',
            404: 'Not found',
        },
        tags=['admin']
    )
    def delete(self, request, *args, **kwargs):
        social_media = SocialMedia.objects.filter(id=kwargs['pk']).first()
        if social_media is None:
            return Response(data={'error': _('SocialMedia not found')}, status=status.HTTP_404_NOT_FOUND)
        social_media.delete()
        return Response(data={'message': 'Social media successfully deleted'}, status=status.HTTP_200_OK)


class ContactInformationViewSet(ViewSet):
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Get Contact Info By Id",
        operation_summary="Get Contact Info By Id",
        responses={
            200: ContactInformationSerializer(),
        },
        tags=['admin']
    )
    def get_by_id(self, request, *args, **kwargs):
        contact_info = ContactInformation.objects.filter(id=kwargs['pk']).first()
        if contact_info is None:
            return Response(data={'error': 'Contact Info not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ContactInformationSerializer(contact_info, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get all Contact Info",
        operation_summary="Get all Contact Info",
        responses={
            200: ContactInformationSerializer(),
        },
        tags=['admin']
    )
    def get_all(self, request, *args, **kwargs):
        contact_info = ContactInformation.objects.all()
        serializer = ContactInformationSerializer(contact_info, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Create Contact Info",
        operation_summary="Create Contact Info",
        manual_parameters=[
            openapi.Parameter(
                name='image',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="image"
            ),
            openapi.Parameter(
                name='location',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="location",
            ),
            openapi.Parameter(
                name='location_uz',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="location_uz",
            ),
            openapi.Parameter(
                name='location_ru',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="location_ru",
            ),
            openapi.Parameter(
                name='location_en',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="location_en",
            ),
            openapi.Parameter(
                name='phone_number',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="phone_number",
            ),
            openapi.Parameter(
                name='email',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="email",
            ),
        ],
        responses={201: SpecialContactInformationSerializer()},
        tags=['admin'],
    )
    def create(self, request, *args, **kwargs):
        serializer = SpecialContactInformationSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Update Contact Info",
        operation_summary="Update Contact Info",
        manual_parameters=[
            openapi.Parameter(
                name='image',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=False,
                description="image"
            ),
            openapi.Parameter(
                name='location',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="location",
            ),
            openapi.Parameter(
                name='location_uz',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="location_uz",
            ),
            openapi.Parameter(
                name='location_ru',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="location_ru",
            ),
            openapi.Parameter(
                name='location_en',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="location_en",
            ),
            openapi.Parameter(
                name='phone_number',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="phone_number",
            ),
            openapi.Parameter(
                name='email',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="email",
            ),
        ],
        responses={200: SpecialContactInformationSerializer()},
        tags=['admin'],
    )
    def update(self, request, *args, **kwargs):
        contact_info = ContactInformation.objects.filter(id=kwargs['pk']).first()
        if contact_info is None:
            return Response(data={'error': 'Contact Info not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SpecialContactInformationSerializer(contact_info, data=request.data, partial=True,
                                                         context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Delete Contact Info",
        operation_summary="Delete Contact Info",
        responses={
            200: 'Successfully deleted',
            404: 'Not found',
        },
        tags=['admin']
    )
    def delete(self, request, *args, **kwargs):
        contact_info = ContactInformation.objects.filter(id=kwargs['pk']).first()
        if contact_info is None:
            return Response(data={'error': 'Contact Info not found'}, status=status.HTTP_404_NOT_FOUND)
        contact_info.delete()
        return Response(data={'message': 'Successfully deleted'}, status=status.HTTP_200_OK)


class AboutResultViewSet(ViewSet):
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Get About Result By Id",
        operation_summary="Get About Result By Id",
        responses={
            200: AboutResultSerializer(),
        },
        tags=['admin']
    )
    def get_by_id(self, request, *args, **kwargs):
        about_result = AboutResult.objects.filter(id=kwargs['pk']).first()
        if about_result is None:
            return Response(data={'error': 'About result not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AboutResultSerializer(about_result, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get all About Result",
        operation_summary="Get all About Result",
        responses={
            200: AboutResultSerializer(),
        },
        tags=['admin']
    )
    def get_all(self, request, *args, **kwargs):
        about_result = AboutResult.objects.all()
        serializer = AboutResultSerializer(about_result, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Create About Result",
        operation_summary="Create About Result",
        manual_parameters=[
            openapi.Parameter(
                name='image',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="image"
            ),
            openapi.Parameter(
                name='description',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="description",
            ),
            openapi.Parameter(
                name='description_uz',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="description_uz",
            ),
            openapi.Parameter(
                name='description_ru',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="description_ru",
            ),
            openapi.Parameter(
                name='description_en',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="description_en",
            ),
        ],
        responses={201: SpecialAboutResultSerializer()},
        tags=['admin'],
    )
    def create(self, request, *args, **kwargs):
        serializer = SpecialAboutResultSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Create About Result",
        operation_summary="Create About Result",
        manual_parameters=[
            openapi.Parameter(
                name='image',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=False,
                description="image"
            ),
            openapi.Parameter(
                name='description',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="description",
            ),
            openapi.Parameter(
                name='description_uz',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="description_uz",
            ),
            openapi.Parameter(
                name='description_ru',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="description_ru",
            ),
            openapi.Parameter(
                name='description_en',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="description_en",
            ),
        ],
        responses={200: SpecialAboutResultSerializer()},
        tags=['admin'],
    )
    def update(self, request, *args, **kwargs):
        about_result = AboutResult.objects.filter(id=kwargs['pk']).first()
        if about_result is None:
            return Response(data={'error': 'About result not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SpecialAboutResultSerializer(about_result, data=request.data, partial=True,
                                                  context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Delete About Result",
        operation_summary="Delete About Result",
        responses={
            200: 'Successfully deleted',
            404: 'Not found',
        },
        tags=['admin']
    )
    def delete(self, request, *args, **kwargs):
        about_result = AboutResult.objects.filter(id=kwargs['pk']).first()
        if about_result is None:
            return Response(data={'error': 'About result not found'}, status=status.HTTP_404_NOT_FOUND)
        about_result.delete()
        return Response(data={'message': 'Successfully deleted'}, status=status.HTTP_200_OK)


class AboutUsViewSet(ViewSet):
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Get About Us By Id",
        operation_summary="Get About Us By Id",
        responses={
            200: AboutUsSerializer(),
        },
        tags=['admin']
    )
    def get_by_id(self, request, *args, **kwargs):
        about_us = AboutUs.objects.filter(id=kwargs['pk']).first()
        if about_us is None:
            return Response(data={'error': 'About us not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AboutUsSerializer(about_us, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get all About Us",
        operation_summary="Get all About Us",
        responses={
            200: AboutUsSerializer(),
        },
        tags=['admin']
    )
    def get_all(self, request, *args, **kwargs):
        about_us = AboutUs.objects.all()
        serializer = AboutUsSerializer(about_us, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Update About Us",
        operation_summary="Update About Us",
        manual_parameters=[
            openapi.Parameter(
                name='title',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="title"
            ),openapi.Parameter(
                name='title_uz',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="title_uz"
            ),openapi.Parameter(
                name='title_ru',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="title_ru"
            ),openapi.Parameter(
                name='title_en',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="title_en"
            ),
            openapi.Parameter(
                name='sub_title',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="sub_title",
            ),
            openapi.Parameter(
                name='sub_title_uz',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="sub_title_uz",
            ),
            openapi.Parameter(
                name='sub_title_ru',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="sub_title_ru",
            ),
            openapi.Parameter(
                name='sub_title_en',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="sub_title_en",
            ),
            openapi.Parameter(
                name='description',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="description",
            ),
            openapi.Parameter(
                name='description_uz',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="description_uz",
            ),
            openapi.Parameter(
                name='description_ru',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="description_ru",
            ),
            openapi.Parameter(
                name='description_en',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="description_en",
            ),
            openapi.Parameter(
                name='founder_name',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="founder_name",
            ),
            openapi.Parameter(
                name='founder_position',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="founder_position",
            ),
            openapi.Parameter(
                name='founder_position_uz',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="founder_position_uz",
            ),
            openapi.Parameter(
                name='founder_position_ru',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="founder_position_ru",
            ),
            openapi.Parameter(
                name='founder_position_en',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="founder_position_en",
            ),
            openapi.Parameter(
                name='founder_image',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="founder_image",
            ),
            openapi.Parameter(
                name='co_founder_name',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="co_founder_name",
            ),
            openapi.Parameter(
                name='co_founder_position',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="co_founder_position",
            ),
            openapi.Parameter(
                name='co_founder_position_uz',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="co_founder_position_uz",
            ),
            openapi.Parameter(
                name='co_founder_position_ru',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="co_founder_position_ru",
            ),
            openapi.Parameter(
                name='co_founder_position_en',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="co_founder_position_en",
            ),
            openapi.Parameter(
                name='co_founder_image',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="co_founder_image",
            ),
        ],
        responses={201: SpecialAboutUsSerializer()},
        tags=['admin'],
    )
    def create(self, request, *args, **kwargs):
        serializer = SpecialAboutUsSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Update About Us",
        operation_summary="Update About Us",
        manual_parameters=[
            openapi.Parameter(
                name='title',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="title"
            ), openapi.Parameter(
                name='title_uz',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="title_uz"
            ), openapi.Parameter(
                name='title_ru',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="title_ru"
            ), openapi.Parameter(
                name='title_en',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="title_en"
            ),
            openapi.Parameter(
                name='sub_title',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="sub_title",
            ),
            openapi.Parameter(
                name='sub_title_uz',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="sub_title_uz",
            ),
            openapi.Parameter(
                name='sub_title_ru',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="sub_title_ru",
            ),
            openapi.Parameter(
                name='sub_title_en',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="sub_title_en",
            ),
            openapi.Parameter(
                name='description',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="description",
            ),
            openapi.Parameter(
                name='description_uz',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="description_uz",
            ),
            openapi.Parameter(
                name='description_ru',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="description_ru",
            ),
            openapi.Parameter(
                name='description_en',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="description_en",
            ),
            openapi.Parameter(
                name='founder_name',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="founder_name",
            ),
            openapi.Parameter(
                name='founder_position',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="founder_position",
            ),
            openapi.Parameter(
                name='founder_position_uz',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="founder_position_uz",
            ),
            openapi.Parameter(
                name='founder_position_ru',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="founder_position_ru",
            ),
            openapi.Parameter(
                name='founder_position_en',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="founder_position_en",
            ),
            openapi.Parameter(
                name='founder_image',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=False,
                description="founder_image",
            ),
            openapi.Parameter(
                name='co_founder_name',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="co_founder_name",
            ),
            openapi.Parameter(
                name='co_founder_position',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="co_founder_position",
            ),
            openapi.Parameter(
                name='co_founder_position_uz',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="co_founder_position_uz",
            ),
            openapi.Parameter(
                name='co_founder_position_ru',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="co_founder_position_ru",
            ),
            openapi.Parameter(
                name='co_founder_position_en',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="co_founder_position_en",
            ),
            openapi.Parameter(
                name='co_founder_image',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=False,
                description="co_founder_image",
            ),
        ],
        responses={200: SpecialAboutUsSerializer()},
        tags=['admin'],
    )
    def update(self, request, *args, **kwargs):
        about_us = AboutUs.objects.filter(id=kwargs['pk']).first()
        if about_us is None:
            return Response(data={'error': 'About us not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SpecialAboutUsSerializer(about_us, data=request.data, partial=True, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Delete About Us",
        operation_summary="Delete About Us",
        responses={
            200: 'Successfully deleted',
            404: 'Not found',
        },
        tags=['admin']
    )
    def delete(self, request, *args, **kwargs):
        about_us = AboutUs.objects.filter(id=kwargs['pk']).first()
        if about_us is None:
            return Response(data={'error': 'About us not found'}, status=status.HTTP_404_NOT_FOUND)
        about_us.delete()
        return Response(data={'message': 'Successfully deleted'}, status=status.HTTP_200_OK)


class PolicyViewSet(ViewSet):
    @swagger_auto_schema(
        operation_description="Get Policy By Id",
        operation_summary="Get Policy By Id",
        responses={
            200: PolicySerializer(),
        },
        tags=['admin']
    )
    def get_by_id(self, request, *args, **kwargs):
        policy = Policy.objects.filter(id=kwargs['pk']).first()
        if policy is None:
            return Response(data={'error': 'Policy not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = PolicySerializer(policy, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get all Policy",
        operation_summary="Get all Policy",
        responses={
            200: PolicySerializer(),
        },
        tags=['admin']
    )
    def get_all(self, request, *args, **kwargs):
        policy = Policy.objects.all()
        serializer = PolicySerializer(policy, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Create Policy",
        operation_summary="Create Policy",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='description'),
                'description_uz': openapi.Schema(type=openapi.TYPE_STRING, description='description_uz'),
                'description_ru': openapi.Schema(type=openapi.TYPE_STRING, description='description_ru'),
                'description_en': openapi.Schema(type=openapi.TYPE_STRING, description='description_en'),
            },
            required=['description', 'description_uz', 'description_ru', 'description_en']
        ),
        responses={201: SpecialPolicySerializer()},
        tags=['admin'],
    )
    def create(self, request, *args, **kwargs):
        serializer = SpecialPolicySerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Update Policy",
        operation_summary="Update Policy",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='description'),
                'description_uz': openapi.Schema(type=openapi.TYPE_STRING, description='description_uz'),
                'description_ru': openapi.Schema(type=openapi.TYPE_STRING, description='description_ru'),
                'description_en': openapi.Schema(type=openapi.TYPE_STRING, description='description_en'),
            },
            required=[]
        ),
        responses={200: SpecialPolicySerializer()},
        tags=['admin'],
    )
    def update(self, request, *args, **kwargs):
        policy = Policy.objects.filter(id=kwargs['pk']).first()
        if policy is None:
            return Response(data={'error': 'Policy not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SpecialPolicySerializer(policy, data=request.data, partial=True, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Delete Policy",
        operation_summary="Delete Policy",
        responses={
            200: 'Successfully deleted',
            404: 'Not found',
        },
        tags=['admin']
    )
    def delete(self, request, *args, **kwargs):
        policy = Policy.objects.filter(id=kwargs['pk']).first()
        if policy is None:
            return Response(data={'error': 'Policy not found'}, status=status.HTTP_404_NOT_FOUND)
        policy.delete()
        return Response(data={'message': 'Successfully deleted'}, status=status.HTTP_200_OK)


class WebResultImageViewSet(ViewSet):
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Get Result Image By Id",
        operation_summary="Get Result Image By Id",
        responses={
            200: ResultImageSerializer(),
        },
        tags=['admin']
    )
    def get_by_id(self, request, *args, **kwargs):
        web_res = ResultImage.objects.filter(id=kwargs['pk']).first()
        if web_res is None:
            return Response(data={'error': 'Result image not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ResultImageSerializer(web_res, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get all Result Image",
        operation_summary="Get all Result Image",
        responses={
            200: ResultImageSerializer(),
        },
        tags=['admin']
    )
    def get_all(self, request, *args, **kwargs):
        web_res = ResultImage.objects.all()
        serializer = ResultImageSerializer(web_res, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Create Result Image",
        operation_summary="Create Result Image",
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
            ),
        ],
        responses={201: ResultImageSerializer()},
        tags=['admin'],
    )
    def create(self, request, *args, **kwargs):
        serializer = ResultImageSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Update Result Image",
        operation_summary="Update Result Image",
        manual_parameters=[
            openapi.Parameter(
                name='image',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=False,
                description="image"
            ),
            openapi.Parameter(
                name='name',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="name",
            ),
        ],
        responses={200: ResultImageSerializer()},
        tags=['admin'],
    )
    def update(self, request, *args, **kwargs):
        web_res = ResultImage.objects.filter(id=kwargs['pk']).first()
        if web_res is None:
            return Response(data={'error': 'Result image not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ResultImageSerializer(web_res, data=request.data, partial=True, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Delete Result Image",
        operation_summary="Delete Result Image",
        responses={
            200: 'Successfully deleted',
            404: 'Not found',
        },
        tags=['admin']
    )
    def delete(self, request, *args, **kwargs):
        web_res = ResultImage.objects.filter(id=kwargs['pk']).first()
        if web_res is None:
            return Response(data={'error': 'Result image not found'}, status=status.HTTP_404_NOT_FOUND)
        web_res.delete()
        return Response(data={'message': 'Successfully deleted'}, status=status.HTTP_200_OK)


class ContactUsViewSet(ViewSet):
    pagination_class = CustomPagination

    @swagger_auto_schema(
        operation_description="Get Contact Us By Id",
        operation_summary="Get Contact Us By Id",
        responses={
            200: ContactUsSerializer(),
        },
        tags=['admin']
    )
    def get_by_id(self, request, *args, **kwargs):
        contact_us = ContactUs.objects.filter(id=kwargs['pk']).first()
        if contact_us is None:
            return Response(data={'error': 'Contact us not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ContactUsSerializer(contact_us, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

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
            return Response(data={'error': _('Size or Page is needed')}, status=status.HTTP_400_BAD_REQUEST)
        if not page.isdigit() or int(page) < 1:
            return Response(data={'error': _('page must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        if not size.isdigit() or int(size) < 1:
            return Response(data={'error': _('page size must be greater than 0 or must be integer')},
                            status=status.HTTP_400_BAD_REQUEST)
        contact_us = ContactUs.objects.all()
        paginator = self.pagination_class()
        paginated_contact_us = paginator.paginate_queryset(contact_us, request)
        serializer = ContactUsSerializer(paginated_contact_us, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Update Contact Us",
        operation_summary="update Contact Us",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'replied': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='replied'),
            },
            required=['replied']
        ),
        responses={200: ContactUsSerializer()},
        tags=['admin'],
    )
    def update(self, request, *args, **kwargs):
        contact_us = ContactUs.objects.filter(id=kwargs['pk']).first()
        if contact_us is None:
            return Response(data={'error': 'Contact us not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ContactUsSerializer(contact_us, data=request.data, partial=True, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Delete Contact Info",
        operation_summary="Delete Contact Info",
        responses={
            200: 'Successfully deleted',
            404: 'Not found',
        },
        tags=['admin']
    )
    def delete(self, request, *args, **kwargs):
        contact_us = ContactUs.objects.filter(id=kwargs['pk']).first()
        if contact_us is None:
            return Response(data={'error': 'Contact us not found'}, status=status.HTTP_404_NOT_FOUND)
        contact_us.delete()
        return Response(data={'message': 'Successfully deleted'}, status=status.HTTP_200_OK)
