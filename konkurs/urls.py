from django.urls import path
from .views import (
    CompetitionViewSet,
    MyCompetitionViewSet,
    ContactUsViewSet
)

urlpatterns = [
    path('get_main_banner/', CompetitionViewSet.as_view({'get': 'get_main_banner'}), name='get_main_banner'),
    # competitions for home page
    path('get_home_page_competitions/', CompetitionViewSet.as_view({'get': 'get_comp_for_home'}),
         name='get_home_page_competitions'),
    # competitions for competitions page
    path('get_competitions/', CompetitionViewSet.as_view({'get': 'get_comp'}), name='get_competitions'),
    path('get_gallery/', CompetitionViewSet.as_view({'get': 'get_gallery'}), name='get_gallery'),
    path('get_experts/', CompetitionViewSet.as_view({'get': 'get_experts'}), name='get_experts'),
    path('get_results/', CompetitionViewSet.as_view({'get': 'get_results'}), name='get_results'),
    path('get_comp_by_id/<int:pk>/', CompetitionViewSet.as_view({'get': 'get_by_id'}),
         name='get_comp_details'),
    path('get_gallery_details/<int:pk>/', CompetitionViewSet.as_view({'get': 'get_gallery_details'}),
         name='get_gallery_details'),
    # my competition
    path('get_comp_details/<int:pk>/', MyCompetitionViewSet.as_view({'get': 'get_comp_details'}), name='comp_detail'),
    path('get_active_competitions/', MyCompetitionViewSet.as_view({'get': 'active'}), name='get_active_competitions'),
    path('get_finished_competitions/', MyCompetitionViewSet.as_view({'get': 'finished'}),
         name='get_finished_competitions'),
    # grade history
    path('get_grade_history/', MyCompetitionViewSet.as_view({'get': 'get_grade_history'}), name='get_grade_history'),
    path('get_grade_by_id/<int:pk>/', MyCompetitionViewSet.as_view({'get': 'get_grade_history_by_id'}),
         name='get_grade_history_by_id'),
    path('get_notifications/', MyCompetitionViewSet.as_view({'get': 'get_notifications'}), name='get_notifications'),
    path('get_notification_by_id/<int:pk>/', MyCompetitionViewSet.as_view({'get': 'get_notification_by_id'}),
         name='get_notification_by_id'),
    # path('', MyCompetitionViewSet.as_view({'get': 'subscriptions'})),
    path('contact_us/', ContactUsViewSet.as_view({'post': 'create'}), name='contact_us'),

]
