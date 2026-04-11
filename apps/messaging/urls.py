from rest_framework.routers import DefaultRouter

from .views import OutgoingMessageViewSet

router = DefaultRouter()
router.register(r"messages", OutgoingMessageViewSet, basename="outgoing-message")

urlpatterns = router.urls
