from django.urls import path
from .views import ClickWebhookAPIView

urlpatterns = [
    path("payment/click/update/", ClickWebhookAPIView.as_view()),
]