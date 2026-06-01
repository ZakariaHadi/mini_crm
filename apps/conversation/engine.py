from __future__ import annotations

import logging
from typing import Any

from apps.main_crm.models import Business
from apps.chatbot_builder.models import Node, Option
from infrastructure.redis import session_store

from .actions import execute_action
from .renderers import render_node
from .services import persist_conversation

logger = logging.getLogger(__name__)

BACK_COMMAND = "0"
RESTART_COMMAND = "#"

FLOW_WAIT_MESSAGE = "Veuillez compléter le formulaire ouvert."


class ConversationEngine:
    """
    Stateless engine that processes incoming messages against the chatbot graph.
    Session state lives in Redis, config in Postgres.
    """

    def process(self, business: Business, phone: str, message: str) -> str | dict[str, Any] | None:
        session = session_store.get(business.id, phone)

        if session is None:
            return self._start_session(business, phone)

        if session.get("active_flow"):
            return FLOW_WAIT_MESSAGE

        chatbot = business.chatbots.filter(is_active=True).first()
        if chatbot is None:
            logger.error("No active chatbot for business %s", business.pk)
            return "Service temporairement indisponible."

        if message == BACK_COMMAND and chatbot.enable_back:
            return self._go_back(business, phone, session)

        if message == RESTART_COMMAND and chatbot.enable_restart:
            return self._restart(business, phone)

        try:
            node = Node.objects.select_related("chatbot").get(id=session["current_node_id"])
        except Node.DoesNotExist:
            logger.error("Node %s not found, restarting", session["current_node_id"])
            return self._restart(business, phone)

        option = self._resolve_option(node, message)
        if option is None:
            return "Choix invalide. Veuillez réessayer."

        session["collected_data"][str(node.id)] = option.value
        session["history"].append(node.id)

        if option.action:
            result = execute_action(option.action, phone, session)
            if result is not None:
                session_store.save(business.id, phone, result)
                return None

        next_node = option.next_node
        if next_node is None or next_node.type == Node.NodeType.END:
            persist_conversation(business, phone, session)
            session_store.delete(business.id, phone)
            return next_node.content.get("text", "Merci !") if next_node else "Merci !"

        session["current_node_id"] = next_node.id
        session_store.save(business.id, phone, session)
        return render_node(next_node)

    def _start_session(self, business: Business, phone: str) -> str | dict[str, Any]:
        start_node = (
            Node.objects.filter(chatbot__business=business, is_start=True)
            .select_related("chatbot")
            .first()
        )
        if start_node is None:
            logger.error("No start node for business %s", business.pk)
            return "Aucun chatbot configuré."

        session: dict[str, Any] = {
            "current_node_id": start_node.id,
            "history": [],
            "collected_data": {},
        }
        session_store.save(business.id, phone, session)
        return render_node(start_node)

    def _go_back(
        self,
        business: Business,
        phone: str,
        session: dict[str, Any],
    ) -> str | dict[str, Any]:
        if not session["history"]:
            return self._restart(business, phone)

        prev_id = session["history"].pop()
        session["current_node_id"] = prev_id
        session_store.save(business.id, phone, session)

        node = Node.objects.get(id=prev_id)
        return render_node(node)

    def _restart(self, business: Business, phone: str) -> str | dict[str, Any]:
        session_store.delete(business.id, phone)
        return self._start_session(business, phone)

    @staticmethod
    def _resolve_option(node: Node, message: str) -> Option | None:
        return node.options.filter(value=message).select_related("next_node").first()


conversation_engine = ConversationEngine()
