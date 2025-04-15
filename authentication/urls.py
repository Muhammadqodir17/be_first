from django.urls import path
from .views import RegistrationViewSet, LoginViewSet

urlpatterns = [
    path('send_sms/', RegistrationViewSet.as_view({'post': 'send_sms'}), name='send_sms'),
    path('verify_sms/', RegistrationViewSet.as_view({'post': 'verify_sms'}), name='verify_sms'),
    path('set_password/', RegistrationViewSet.as_view({'post': 'set_password'}), name='set_password'),
    path('user/', RegistrationViewSet.as_view({'get': 'get_user'}), name='get_user_for_set_profile'),
    path('set_profile/', RegistrationViewSet.as_view({'post': 'set_profile'}), name='set_profile'),
    path('login/', LoginViewSet.as_view({'get': 'login_user'}), name='login'),
    path('forgot_password/', LoginViewSet.as_view({'post': 'send_temp_password'}), name='forgot_password'),
    path('reset_password/', LoginViewSet.as_view({'post': 'reset_password'}), name='reset_password'),
]
