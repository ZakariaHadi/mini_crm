from __future__ import annotations

import logging
from typing import Any

from apps.main_crm.models import Business
from apps.chatbot_builder.models import Node
from apps.conversation.renderers import render_node
from apps.messaging.tasks import send_message_task
from infrastructure.redis import session_store

logger = logging.getLogger(__name__)


def handle_whatsapp_flow_response(
    business: Business, phone: str, flow_response: dict[str, Any]
) -> None:
    """
    Process a completed WhatsApp Flow response:
    1. Validate flow_id matches active session flow
    2. Inject collected data into session
    3. Clear active_flow
    4. Resume chatbot from return_node or current_node
    5. Send the next message
    """
    session = session_store.get(business.id, phone)
    if session is None:
        logger.warning("Flow response for unknown session: %s %s", business.pk, phone)
        return

    active_flow = session.get("active_flow")
    if not active_flow:
        logger.warning("Flow response but no active_flow in session: %s", phone)
        return

    response_flow_id = flow_response.get("flow_id", "")
    if active_flow["flow_id"] != response_flow_id:
        logger.warning(
            "Flow ID mismatch: expected %s, got %s",
            active_flow["flow_id"],
            response_flow_id,
        )
        return

    flow_data = flow_response.get("data", {})
    session["collected_data"].update(flow_data)

    return_node_id = active_flow.get("return_node_id")
    session.pop("active_flow")

    if return_node_id:
        session["current_node_id"] = return_node_id

    session_store.save(business.id, phone, session)

    try:
        node = Node.objects.get(id=session["current_node_id"])
    except Node.DoesNotExist:
        logger.error("Return node %s not found", session["current_node_id"])
        return

    response = render_node(node)
    if response:
        send_message_task.delay(phone, response)
