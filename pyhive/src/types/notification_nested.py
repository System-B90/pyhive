"""
Name: notification_nested.py
Purpose: Model definition for a nested notification in the Hive system.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from typing import Annotated,TYPE_CHECKING, Any, Self, TypeVar

from pydantic import Field, PrivateAttr

from .core_item import HiveCoreItem

if TYPE_CHECKING:
    from ...client import HiveClient
    from .user import User


class NotificationNested(HiveCoreItem):
    """A lightweight notification model.

    Attributes:
        id: Unique identifier of the notification.
        from_user_id: Optional user ID that sent the notification.
        comment: Optional comment text.

    """

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]
    id: int
    from_user_id: int | None = Field(default=None, alias="from_user")
    comment: str | None = Field(default=None)

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
