from __future__ import annotations

import logging
from typing import Any

import httpx
from celery import shared_task
from django.db.models import F

from infrastructure.whatsapp_client import whatsapp_client

from .models import OutgoingMessage

logger = logging.getLogger(__name__)

MAX_RETRIES = 5


@shared_task(bind=True, max_retries=MAX_RETRIES, acks_late=True)
def send_message_task(
    self: Any, phone: str, payload: str | dict[str, Any]
) -> dict[str, Any] | None:
    """Send a text or structured message via WhatsApp and track delivery."""
    msg = OutgoingMessage.objects.create(
        phone=phone,
        content=payload if isinstance(payload, dict) else {"text": payload},
    )

    try:
        if isinstance(payload, str):
            result = whatsapp_client.send_text(phone, payload)
        elif isinstance(payload, dict) and payload.get("type") == "template":
            result = whatsapp_client.send_template(
                phone, payload["template_name"], payload.get("language", "fr")
            )
        elif isinstance(payload, dict) and payload.get("type") == "flow":
            result = whatsapp_client.send_flow(
                phone,
                flow_id=payload["flow_id"],
                body_text=payload.get("body_text", "Continuer"),
                flow_cta=payload.get("flow_cta", "Ouvrir"),
                screen=payload.get("screen"),
            )
        else:
            result = whatsapp_client.send_text(phone, str(payload))

        provider_id = result.get("messages", [{}])[0].get("id")
        msg.status = OutgoingMessage.Status.SENT
        msg.provider_message_id = provider_id
        msg.save(update_fields=["status", "provider_message_id", "updated_at"])
        return result

    except httpx.HTTPStatusError as exc:
        return _handle_error(self, msg, exc, exc.response.status_code)
    except httpx.RequestError as exc:
        return _handle_error(self, msg, exc, 0)


@shared_task(bind=True, max_retries=MAX_RETRIES, acks_late=True)
def send_template_task(
    self: Any, phone: str, template_name: str, language: str = "fr"
) -> dict[str, Any] | None:
    msg = OutgoingMessage.objects.create(
        phone=phone,
        content={"type": "template", "template_name": template_name},
    )
    try:
        result = whatsapp_client.send_template(phone, template_name, language)
        provider_id = result.get("messages", [{}])[0].get("id")
        msg.status = OutgoingMessage.Status.SENT
        msg.provider_message_id = provider_id
        msg.save(update_fields=["status", "provider_message_id", "updated_at"])
        return result
    except httpx.HTTPStatusError as exc:
        return _handle_error(self, msg, exc, exc.response.status_code)
    except httpx.RequestError as exc:
        return _handle_error(self, msg, exc, 0)


@shared_task(bind=True, max_retries=3, acks_late=True)
def external_api_call_task(
    self: Any,
    url: str,
    method: str = "POST",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.request(method, url, json=payload)
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPStatusError, httpx.RequestError) as exc:
        logger.error("External API call failed: %s", exc)
        raise self.retry(countdown=2**self.request.retries, exc=exc)


def _handle_error(
    task: Any,
    msg: OutgoingMessage,
    exc: Exception,
    status_code: int,
) -> None:
    OutgoingMessage.objects.filter(pk=msg.pk).update(
        retry_count=F("retry_count") + 1,
        error_detail=str(exc)[:500],
    )

    if status_code >= 500 or status_code == 0:
        logger.warning(
            "Retryable error for message %s (attempt %d): %s",
            msg.pk,
            task.request.retries,
            exc,
        )
        raise task.retry(countdown=2**task.request.retries, exc=exc)

    msg.status = OutgoingMessage.Status.FAILED
    msg.save(update_fields=["status", "updated_at"])
    logger.error("Fatal error for message %s: %s", msg.pk, exc)
