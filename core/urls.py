from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def healthcheck(request: Request) -> Response:
    return Response({"status": "healthy"})


urlpatterns = [
    path("admin/", admin.site.urls),
    # Healthcheck
    path("health/", healthcheck, name="healthcheck"),
    # API v1
    path("api/v1/accounts/", include("apps.accounts.urls")),
    path("api/v1/chatbot/", include("apps.chatbot_builder.urls")),
    path("api/v1/conversations/", include("apps.conversation.urls")),
    path("api/v1/messaging/", include("apps.messaging.urls")),
    path("api/v1/integrations/", include("apps.integrations.urls")),
    # OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
