from __future__ import annotations

import logging
from typing import Any

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """
    Production-grade WhatsApp Cloud API client.
    Uses httpx for connection pooling and proper timeout handling.
    """

    def __init__(self) -> None:
        self.base_url: str = settings.WHATSAPP_API_URL
        self.phone_number_id: str = settings.WHATSAPP_PHONE_NUMBER_ID
        self.token: str = settings.WHATSAPP_API_TOKEN

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    @property
    def _messages_url(self) -> str:
        return f"{self.base_url}/{self.phone_number_id}/messages"

    def send_text(self, phone: str, text: str) -> dict[str, Any]:
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"body": text},
        }
        return self._post(payload)

    def send_template(self, phone: str, template_name: str, language: str = "fr") -> dict[str, Any]:
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
            },
        }
        return self._post(payload)

    def send_interactive_buttons(
        self,
        phone: str,
        body_text: str,
        buttons: list[dict[str, str]],
        header: str | None = None,
        footer: str | None = None,
    ) -> dict[str, Any]:
        action_buttons = [
            {"type": "reply", "reply": {"id": b["id"], "title": b["title"]}}
            for b in buttons[:3]  # WhatsApp max 3 buttons
        ]
        interactive: dict[str, Any] = {
            "type": "button",
            "body": {"text": body_text},
            "action": {"buttons": action_buttons},
        }
        if header:
            interactive["header"] = {"type": "text", "text": header}
        if footer:
            interactive["footer"] = {"text": footer}

        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "interactive",
            "interactive": interactive,
        }
        return self._post(payload)

    def send_flow(
        self,
        phone: str,
        flow_id: str,
        flow_token: str = "",
        header: str | None = None,
        body_text: str = "Continuer",
        footer: str | None = None,
        flow_cta: str = "Ouvrir",
        screen: str | None = None,
        flow_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a WhatsApp Flow (native rich UI)."""
        flow_action_payload: dict[str, Any] = {}
        if screen:
            flow_action_payload["screen"] = screen
        if flow_data:
            flow_action_payload["data"] = flow_data

        interactive: dict[str, Any] = {
            "type": "flow",
            "body": {"text": body_text},
            "action": {
                "name": "flow",
                "parameters": {
                    "flow_message_version": "3",
                    "flow_id": flow_id,
                    "flow_token": flow_token or f"flow_{flow_id}_{phone}",
                    "flow_cta": flow_cta,
                    "flow_action": "navigate",
                    "flow_action_payload": flow_action_payload,
                },
            },
        }
        if header:
            interactive["header"] = {"type": "text", "text": header}
        if footer:
            interactive["footer"] = {"text": footer}

        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "interactive",
            "interactive": interactive,
        }
        return self._post(payload)

    def send_interactive_list(
        self,
        phone: str,
        body_text: str,
        button_text: str,
        sections: list[dict[str, Any]],
    ) -> dict[str, Any]:
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {"text": body_text},
                "action": {
                    "button": button_text,
                    "sections": sections,
                },
            },
        }
        return self._post(payload)

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    self._messages_url,
                    json=payload,
                    headers=self._headers,
                )
                response.raise_for_status()
                data: dict[str, Any] = response.json()
                logger.info(
                    "WhatsApp message sent to %s — id=%s",
                    payload.get("to"),
                    data.get("messages", [{}])[0].get("id"),
                )
                return data
        except httpx.HTTPStatusError as exc:
            logger.error(
                "WhatsApp API error %s: %s",
                exc.response.status_code,
                exc.response.text,
            )
            raise
        except httpx.RequestError as exc:
            logger.error("WhatsApp request failed: %s", exc)
            raise


whatsapp_client = WhatsAppClient()
