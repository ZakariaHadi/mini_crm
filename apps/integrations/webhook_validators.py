from __future__ import annotations

import hashlib
import hmac
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def verify_whatsapp_signature(payload: bytes, signature_header: str) -> bool:
    """
    Verify Meta webhook signature using HMAC SHA256.
    https://developers.facebook.com/docs/graph-api/webhooks/getting-started#verification-requests
    """
    if not settings.WHATSAPP_APP_SECRET:
        logger.warning("WHATSAPP_APP_SECRET not set — skipping signature check")
        return True

    expected = hmac.new(
        settings.WHATSAPP_APP_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    received = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, received)
