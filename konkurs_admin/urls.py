from django.urls import path
from .views import (
    CategoryViewSet,
    CompetitionViewSet,
    JuryViewSet
)

urlpatterns = [
    # category
    path('get_categories/', CategoryViewSet.as_view({'get': 'get'}), name='get_categories'),
    path('get_category_by_id/<int:pk>/', CategoryViewSet.as_view({'get': 'get_by_id'}), name='get_category_by_id'),
    path('create_category/', CategoryViewSet.as_view({'post': 'create'}), name='create_category'),
    path('update_category/<int:pk>/', CategoryViewSet.as_view({'patch': 'update'}), name='update_category'),
    path('delete_category/<int:pk>/', CategoryViewSet.as_view({'delete': 'delete'}), name='delete_category'),
    # competition
    path('get_participants/<int:pk>/', CompetitionViewSet.as_view({'get': 'participants'}), name='get_participants'),
    path('search_participant/<int:pk>/', CompetitionViewSet.as_view({'get': 'search_participant'}),
         name='search_participant'),  #
    path('get_winners/<int:pk>/', CompetitionViewSet.as_view({'get': 'winners'}), name='get_winners'),
    path('search_winners/<int:pk>/', CompetitionViewSet.as_view({'get': 'search_winners'}), name='search_winners'),  #
    path('get_competitions/', CompetitionViewSet.as_view({'get': 'get_comp'}), name='get_competitions'),
    path('search_comp/', CompetitionViewSet.as_view({'get': 'search_comp'}), name='search_comp'),  #
    path('filter_comp/', CompetitionViewSet.as_view({'get': 'filter_comp'}), name='filter_comp'),
    path('get_competition/<int:pk>/', CompetitionViewSet.as_view({'get': 'get_comp_by_id'}),
         name='get_competition_by_id'),
    path('create_competition/', CompetitionViewSet.as_view({'post': 'create_comp'}), name='create_competition'),
    path('update_competition/<int:pk>/', CompetitionViewSet.as_view({'patch': 'update_comp'}),
         name='update_competition'),
    path('delete_competition/<int:pk>/', CompetitionViewSet.as_view({'delete': 'delete_comp'}),
         name='delete_competition'),
    path('participant_requests/<int:pk>/', CompetitionViewSet.as_view({'get': 'participants_requests'}),
         name='participant_requests'),
    path('approvement/<int:pk>/', CompetitionViewSet.as_view({'post': 'approve'}),
         name='request_action'),
    path('active_participants/<int:pk>/', CompetitionViewSet.as_view({'get': 'active_participants'}),
         name='active_participants'),
    path('create_winners/<int:pk>/', CompetitionViewSet.as_view({'post': 'create_winners'}), name='create_winners'),
    path('others/<int:pk>/', CompetitionViewSet.as_view({'get': 'others'}), name='others'),
    path('send_thank_you_message/<int:pk>/', CompetitionViewSet.as_view({'post': 'send_thank_you_message'}),
         name='send_thank_you_message'),
    # jury
    path('get_all_juries/', JuryViewSet.as_view({'get': 'get_all'}), name='get_all_juries'),
    path('search_juries/', JuryViewSet.as_view({'get': 'search_juries'}), name='search_juries'),  #
    path('get_jury_by_id/<int:pk>/', JuryViewSet.as_view({'get': 'get_by_id'}), name='get_by_id'),
    path('create_jury/', JuryViewSet.as_view({'post': 'create'}), name='create_jury'),
    path('update_jury/<int:pk>/', JuryViewSet.as_view({'patch': 'update'}), name='update_jury'),
    path('delete_jury/<int:pk>/', JuryViewSet.as_view({'delete': 'delete'}), name='delete_jury'),
]
