from django.urls import path
from .views import (
    RegistrationViewSet,
    LoginViewSet,
    PersonalInfoViewSet,
    OTPVerificationViewSet
)

urlpatterns = [
    path('set_password/', RegistrationViewSet.as_view({'post': 'set_password'}), name='set_password'),
    path('get_user/', RegistrationViewSet.as_view({'get': 'get_user'}), name='get_user_for_set_profile'),
    path('register/', RegistrationViewSet.as_view({'post': 'register'}), name='register'),
    path('verify_otp/', OTPVerificationViewSet.as_view({'post': 'verify'}), name='verify'),
    path('login/', LoginViewSet.as_view({'post': 'login_user'}), name='login'),
    path('logout/', LoginViewSet.as_view({'post': 'logout', }), name='logout'),
    path('forgot_password/', LoginViewSet.as_view({'post': 'send_temp_password'}), name='forgot_password'),
    path('reset_password/', LoginViewSet.as_view({'post': 'reset_password'}), name='reset_password'),
    path('personal_info/', PersonalInfoViewSet.as_view({'patch': 'personal_info'}), name='personal_info'),
]
