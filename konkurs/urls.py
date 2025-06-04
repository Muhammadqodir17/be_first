from django.urls import path
from .views import (
    CompetitionViewSet,
    MyCompetitionViewSet,
    ContactUsViewSet,
    DynamicInfoViewSet,
    SubscriptionViewSet,
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
    # dynamic
    path('get_all_social_media/', DynamicInfoViewSet.as_view({'get': 'get_all_social_media'}),
         name='k_get_all_social_media'),
    path('get_all_contact_info/', DynamicInfoViewSet.as_view({'get': 'get_all_contact_info'}),
         name='k_get_all_contact_info'),
    path('get_all_about_result/', DynamicInfoViewSet.as_view({'get': 'get_all_about_result'}),
         name='k_get_all_about_result'),
    path('get_all_about_us/', DynamicInfoViewSet.as_view({'get': 'get_all_about_us'}), name='get_all_about_us'),
    path('get_all_policy/', DynamicInfoViewSet.as_view({'get': 'get_all_policy'}), name='get_all_policy'),
    path('get_all_result_img/', DynamicInfoViewSet.as_view({'get': 'get_web_result_image'}),
         name='get_all_result_img'),

    # subscription
    path('get_all_subscription/', SubscriptionViewSet.as_view({'get': 'get_all_subscription'}),
         name='get_all_subscription'),
    path('subscription/', SubscriptionViewSet.as_view({'post': 'subscription'}),
         name='subscription'),
    path('unsubscription/', SubscriptionViewSet.as_view({'post': 'unsubscription'}),
         name='unsubscription'),
]
