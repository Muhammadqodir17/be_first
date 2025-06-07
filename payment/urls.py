from django.urls import path
from .views import PaymentViewSet

urlpatterns = [
    path('pay_create/', PaymentViewSet.as_view({'post': 'pay_create'}), name='pay_create'),
    path('pay_pre_apply/', PaymentViewSet.as_view({'post': 'pay_pre_apply'}), name='pay_pre_apply'),
    path('pay_apply/', PaymentViewSet.as_view({'post': 'pay_apply'}), name='pay_apply'),
    path('download_certificate/', PaymentViewSet.as_view({'get': 'download_certificate'}), name='download_certificate'),
]