from __future__ import annotations

from typing import Any

from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request


class IsOwnerOrReadOnly(BasePermission):
    """Allow write operations only to the object's owner."""

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return hasattr(obj, "owner") and obj.owner == request.user


class IsBusinessMember(BasePermission):
    """Ensure user belongs to the business referenced by the object."""

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        business = getattr(obj, "business", None)
        if business is None:
            return False
        return request.user.businesses.filter(pk=business.pk).exists()
