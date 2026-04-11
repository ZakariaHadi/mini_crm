from __future__ import annotations

import json
import logging
from typing import Any

from django.core.cache import cache

logger = logging.getLogger(__name__)


class SessionStore:
    """
    Redis-backed session store for active conversations.
    Uses django-redis cache backend for connection pooling and resilience.
    """

    TTL: int = 60 * 60 * 24  # 24h

    @staticmethod
    def _key(business_id: int, phone: str) -> str:
        return f"session:{business_id}:{phone}"

    def get(self, business_id: int, phone: str) -> dict[str, Any] | None:
        data = cache.get(self._key(business_id, phone))
        if data is None:
            return None
        return json.loads(data) if isinstance(data, str) else data

    def save(self, business_id: int, phone: str, session: dict[str, Any]) -> None:
        cache.set(
            self._key(business_id, phone),
            json.dumps(session),
            timeout=self.TTL,
        )
        logger.debug("Session saved for %s:%s", business_id, phone)

    def delete(self, business_id: int, phone: str) -> None:
        cache.delete(self._key(business_id, phone))
        logger.debug("Session deleted for %s:%s", business_id, phone)


session_store = SessionStore()
