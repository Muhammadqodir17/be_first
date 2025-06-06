"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from konkurs_admin.tasks import check_competition_notifications
from django.conf.urls.i18n import i18n_patterns

admin.site.site_header = 'Competition SYSTEM'
admin.site.site_title = 'Competition SYSTEM'
admin.site.index_title = 'Welcome to dashboard'

schema_view = get_schema_view(
    openapi.Info(
        title="Competition APIv1",
        default_version="v1",
        description="API for project Competition System",
        terms_of_service="",
        contact=openapi.Contact(email="km1728.uz@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

check_competition_notifications.delay()

urlpatterns = i18n_patterns(
    path('admin/', admin.site.urls),
    # urls
    path('api/v1/konkurs/', include('konkurs.urls')),
    path('api/v1/auth/', include('authentication.urls')),
    path('api/v1/child/', include('child.urls')),
    path('api/v1/jury/', include('jury.urls')),
    path('api/v1/admin/', include('konkurs_admin.urls')),
    path('api/v1/payment/', include('payment.urls')),
    # swagger
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # debug = True
    re_path(r'media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT})
)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


