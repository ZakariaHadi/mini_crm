from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def execute_action(
    action: dict[str, Any], phone: str, session: dict[str, Any]
) -> dict[str, Any] | None:
    """
    Dispatch an action triggered by a chatbot option selection.
    Returns the mutated session if a flow was triggered (engine must pause),
    or None for fire-and-forget actions.
    """
    action_type = action.get("type")
    handler = _HANDLERS.get(action_type)
    if handler is None:
        logger.warning("Unknown action type: %s", action_type)
        return None
    return handler(action, phone, session)


def _handle_send_template(action: dict[str, Any], phone: str, session: dict[str, Any]) -> None:
    from apps.messaging.tasks import send_template_task

    send_template_task.delay(phone, action["template_name"])
    return


def _handle_api_call(action: dict[str, Any], phone: str, session: dict[str, Any]) -> None:
    from apps.messaging.tasks import external_api_call_task

    external_api_call_task.delay(
        url=action["url"],
        method=action.get("method", "POST"),
        payload={
            "phone": phone,
            "data": session.get("collected_data", {}),
        },
    )
    return


def _handle_trigger_flow(
    action: dict[str, Any], phone: str, session: dict[str, Any]
) -> dict[str, Any] | None:
    """
    Trigger a WhatsApp Flow. Mutates session with active_flow metadata
    so the engine pauses until the flow response webhook arrives.
    """
    flow_type = action.get("flow_type")
    if flow_type != "whatsapp":
        logger.warning("Unsupported flow_type: %s", flow_type)
        return None

    from apps.messaging.tasks import send_message_task

    flow_id = action["flow_id"]

    session["active_flow"] = {
        "type": "whatsapp",
        "flow_id": flow_id,
        "return_node_id": action.get("return_node_id"),
    }

    send_message_task.delay(
        phone,
        {
            "type": "flow",
            "flow_id": flow_id,
            "body_text": action.get("body_text", "Continuer"),
            "flow_cta": action.get("flow_cta", "Ouvrir"),
            "screen": action.get("screen"),
        },
    )

    return session


_HANDLERS: dict[str, Any] = {
    "send_template": _handle_send_template,
    "api_call": _handle_api_call,
    "trigger_flow": _handle_trigger_flow,
}
