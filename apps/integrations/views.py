from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.models import Business
from apps.conversation.engine import conversation_engine
from apps.messaging.tasks import send_message_task

from .throttles import WebhookThrottle
from .webhook_validators import verify_whatsapp_signature
from .whatsapp_flow import handle_whatsapp_flow_response

logger = logging.getLogger(__name__)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
@throttle_classes([WebhookThrottle])
def whatsapp_webhook_view(request: Request) -> Response:
    """Combined GET (verification) + POST (incoming messages) endpoint."""
    if request.method == "GET":
        return _verify_webhook(request)
    return _process_webhook(request)


def _verify_webhook(request: Request) -> Response:
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return Response(int(challenge), status=status.HTTP_200_OK)

    logger.warning("Webhook verification failed — bad token")
    return Response(
        {"detail": "Verification failed"}, status=status.HTTP_403_FORBIDDEN
    )


def _process_webhook(request: Request) -> Response:
    signature = request.META.get("HTTP_X_HUB_SIGNATURE_256", "")
    if not verify_whatsapp_signature(request.body, signature):
        logger.warning("Invalid webhook signature")
        return Response(
            {"detail": "Invalid signature"}, status=status.HTTP_403_FORBIDDEN
        )

    body: dict[str, Any] = request.data

    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            phone_number_id = value.get("metadata", {}).get("phone_number_id")

            for message in value.get("messages", []):
                _handle_incoming_message(phone_number_id, message)

    return Response({"status": "ok"}, status=status.HTTP_200_OK)


def _handle_incoming_message(
    phone_number_id: str | None, message: dict[str, Any]
) -> None:
    if not phone_number_id:
        logger.warning("Missing phone_number_id in webhook payload")
        return

    sender_phone = message.get("from", "")
    msg_type = message.get("type", "")

    business = _resolve_business(phone_number_id)
    if business is None:
        return

    if msg_type == "text":
        text = message.get("text", {}).get("body", "")
        _dispatch_to_engine(business, sender_phone, text)

    elif msg_type == "interactive":
        interactive = message.get("interactive", {})
        interactive_type = interactive.get("type", "")

        if interactive_type == "nfm_reply":
            _handle_flow_response(business, sender_phone, interactive)
        else:
            reply = (
                interactive.get("button_reply")
                or interactive.get("list_reply")
                or {}
            )
            text = reply.get("id", "")
            _dispatch_to_engine(business, sender_phone, text)

    else:
        logger.info("Ignoring unsupported message type: %s", msg_type)


def _dispatch_to_engine(
    business: Business, phone: str, text: str
) -> None:
    response = conversation_engine.process(business, phone, text)
    if response is not None:
        send_message_task.delay(phone, response)


def _handle_flow_response(
    business: Business, phone: str, interactive: dict[str, Any]
) -> None:
    """Extract nfm_reply payload and delegate to flow handler."""
    nfm_reply = interactive.get("nfm_reply", {})
    response_json = nfm_reply.get("response_json", {})

    if isinstance(response_json, str):
        import json
        try:
            response_json = json.loads(response_json)
        except json.JSONDecodeError:
            logger.error("Invalid flow response_json: %s", response_json)
            return

    flow_id = response_json.get("flow_token", "").split("_")[1] if "_" in response_json.get("flow_token", "") else ""

    flow_response = {
        "flow_id": response_json.get("flow_id", flow_id),
        "data": {k: v for k, v in response_json.items() if k not in ("flow_token", "flow_id")},
    }

    handle_whatsapp_flow_response(business, phone, flow_response)


def _resolve_business(phone_number_id: str) -> Business | None:
    try:
        return Business.objects.get(whatsapp_phone_number_id=phone_number_id)
    except Business.DoesNotExist:
        logger.error("No business found for phone_number_id=%s", phone_number_id)
        return None
