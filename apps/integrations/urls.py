from django.urls import path

from .views import whatsapp_webhook_view

urlpatterns = [
    path("whatsapp/webhook/", whatsapp_webhook_view, name="whatsapp-webhook"),
]
