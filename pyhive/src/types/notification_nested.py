"""
Name: notification_nested.py
Purpose: Model definition for a nested notification in the Hive system.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Annotated, Any, TypeVar

from typing_extensions import Self

from pydantic import Field, PrivateAttr

from ._generated.models import NotificationNested as _NotificationNestedBase

if TYPE_CHECKING:
    from ...client import HiveClient
    from .user import User


class NotificationNested(_NotificationNestedBase):
    """A lightweight notification model. Data fields inherited from the generated base."""

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]

    _from_user: "User | None" = PrivateAttr(default=None)

    @property
    def from_user(self) -> "User | None":
        """Lazily loads and returns the `User` who sent the notification.

        Returns:
            A `User` instance or `None` if not available.

        """
        if self._from_user is None and self.from_user_id is not None:
            self._from_user = self.hive_client.get_user(self.from_user_id)
        return self._from_user

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        """Deserialize the notification from a dictionary."""
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)


T = TypeVar("T", bound="NotificationNested")
