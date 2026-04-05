"""Model definition for a nested notification in the Hive system.

Represents a lightweight notification object, optionally referencing a user and comment.
"""

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self, TypeVar, cast

from attrs import define, field

from .common import UNSET, Unset
from .core_item import HiveCoreItem

if TYPE_CHECKING:
    from ...client import HiveClient
    from .user import User

T = TypeVar("T", bound="NotificationNested")


@define
class NotificationNested(HiveCoreItem):
    """A lightweight notification model.

    Attributes:
        id: Unique identifier of the notification.
        from_user_id: Optional user ID that sent the notification.
        comment: Optional comment text.

    """

    hive_client: "HiveClient"
    id: int
    from_user_id: None | Unset | int = UNSET
    comment: Unset | str = UNSET

    _from_user: "User | None" = field(init=False, default=None)

    @property
    def from_user(self) -> "User | None":
        """Lazily loads and returns the `User` who sent the notification.

        Returns:
            A `User` instance or `None` if not available.

        """
        if (
            self._from_user is None
            and not isinstance(self.from_user_id, Unset)
            and self.from_user_id is not None
        ):
            self._from_user = self.hive_client.get_user(self.from_user_id)
        return self._from_user

    def to_dict(self) -> dict[str, Any]:
        """Serialize the notification to a dictionary."""
        field_dict: dict[str, Any] = {
            "id": self.id,
        }

        if not isinstance(self.from_user_id, Unset):
            field_dict["from_user"] = self.from_user_id

        if not isinstance(self.comment, Unset):
            field_dict["comment"] = self.comment

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any], hive_client: "HiveClient") -> Self:
        """Deserialize the notification from a dictionary."""
        d = dict(src_dict)

        def _parse_from_user(data: object) -> None | Unset | int:
            if data is None or isinstance(data, Unset):
                return data
            return cast("None | Unset | int", data)

        return cls(
            hive_client=hive_client,
            id=d.pop("id"),
            from_user_id=_parse_from_user(d.pop("from_user", UNSET)),
            comment=d.pop("comment", UNSET),
        )
