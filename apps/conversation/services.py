from __future__ import annotations

import logging
from typing import Any

from apps.accounts.models import Business

from .models import Conversation

logger = logging.getLogger(__name__)


def persist_conversation(
    business: Business, phone: str, session: dict[str, Any]
) -> Conversation:
    conversation = Conversation.objects.create(
        business=business,
        user_phone=phone,
        data=session.get("collected_data", {}),
    )
    logger.info(
        "Conversation %s persisted for %s @ %s",
        conversation.pk,
        phone,
        business.name,
    )
    return conversation
