from __future__ import annotations

import logging
from typing import Any

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = exception_handler(exc, context)

    if response is not None:
        if response.status_code == status.HTTP_400_BAD_REQUEST and "detail" not in response.data:
            response.data = {"errors": response.data}
        response.data["status_code"] = response.status_code
        return response

    logger.exception("Unhandled exception: %s", exc)
    return Response(
        {"detail": "An unexpected error occurred.", "status_code": 500},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
