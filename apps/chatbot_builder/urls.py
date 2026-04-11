from rest_framework.routers import DefaultRouter

from .views import ChatbotViewSet, NodeViewSet, OptionViewSet

router = DefaultRouter()
router.register(r"chatbots", ChatbotViewSet, basename="chatbot")
router.register(r"nodes", NodeViewSet, basename="node")
router.register(r"options", OptionViewSet, basename="option")

urlpatterns = router.urls
