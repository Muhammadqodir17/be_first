from django.urls import path
from .views import JuryViewSet

urlpatterns = [
    path('get_active_comp/', JuryViewSet.as_view({'get': 'get_active_comp'}), name='get_active_comp'),
    # path('filter_comp/', JuryViewSet.as_view({'get': 'filter_comp'}), name='filter_comp'),
    path('get_comp_by_id/<int:pk>/', JuryViewSet.as_view({'get': 'get_comp_by_id'}), name='get_comp_by_id'),
    path('filter_participants/<int:pk>/', JuryViewSet.as_view({'get': 'filter_participants'}),
         name='filter_participants'),
    path('get_participant_by_id/<int:pk>/', JuryViewSet.as_view({'get': 'get_participant_by_id'}),
         name='get_participant_by_id'),
    path('mark/', JuryViewSet.as_view({'post': 'mark'}), name='mark'),
    path('get_assessment_history/', JuryViewSet.as_view({'get': 'get_assessment_history'}),
         name='get_assessment_history'),
    path('get_assessment_by_id/<int:pk>/', JuryViewSet.as_view({'get': 'get_assessment_by_id'}),
         name='get_assessment_by_id'),
    path('update_assessment/', JuryViewSet.as_view({'patch': 'update_assessment_history'}),
         name='update_assessment_history'),
]
