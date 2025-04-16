from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

SCHEMA_URL = "https://engine.staging.aiprice.armsit.com" if not settings.DEBUG else None

schema_view = get_schema_view(
    openapi.Info(
        title="Pricing Engine ",
        default_version='v1',
        description="Pricing Engine ",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[],
    url=SCHEMA_URL,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include("scraper.urls")),


# Swagger & Redoc
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
