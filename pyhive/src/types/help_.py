"""
Name: help_.py
Purpose: Model for student help requests.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Annotated, Any, TypeVar

from typing_extensions import Self

from pydantic import Field, PrivateAttr

from ._generated.models import Help as _HelpBase
from .help_response_segel_nested import HelpResponseSegelNested
from .notification_nested import NotificationNested

if TYPE_CHECKING:
    from ...client import HiveClient
    from .exercise import Exercise
    from .user import User


class Help(_HelpBase):
    """A student's help request.

    Scalar/FK fields are inherited from the generated base; the nested
    ``responses`` and ``notifications`` are overridden to PyHive's curated nested
    types and have ``hive_client`` injected in :meth:`from_dict`.
    """

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]
    # Spec serialises for_exercise as a nested Exercise; PyHive exposes the FK id.
    for_exercise_id: int | None = Field(default=None, alias="for_exercise")
    responses: list["HelpResponseSegelNested"]
    notifications: list["NotificationNested"]

    _user: "User | None" = PrivateAttr(default=None)
    _checker: "User | None" = PrivateAttr(default=None)
    _for_exercise: "Exercise | None" = PrivateAttr(default=None)

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        """
        Deserializes a Help instance from a dictionary payload.

        Args:
            src_dict (dict[str, Any]): The raw dictionary from the API response.
            hive_client (HiveClient): The client instance for deferred network operations.

        Returns:
            Self: An instantiated and validated Help model.
        """
        data = dict(src_dict)
        data["hive_client"] = hive_client
        for response in data.get("responses", []):
            if isinstance(response, dict):
                response["hive_client"] = hive_client

        for notification in data.get("notifications", []):
            if isinstance(notification, dict):
                notification["hive_client"] = hive_client
        return cls.model_validate(data)

    @property
    def for_exercise(self) -> "Exercise | None":
        """
        Lazily loads and returns the related Exercise, if any.

        Returns:
            Exercise | None: The resolved Exercise instance or None when not set.
        """
        if self.for_exercise_id is None:
            return None
        if self._for_exercise is None:
            self._for_exercise = self.hive_client.get_exercise(self.for_exercise_id)
        return self._for_exercise

    @property
    def user(self) -> "User":
        """
        Lazily loads the user who opened this help request.

        Returns:
            User: The associated user instance.
        """
        if self._user is None:
            self._user = self.hive_client.get_user(self.user_id)
        return self._user

    @property
    def checker(self) -> "User | None":
        """
        Lazily loads the assigned checker, if any.

        Returns:
            User | None: The associated checker instance or None when not set.
        """
        if self.checker_id is None:
            return None
        if self._checker is None:
            self._checker = self.hive_client.get_user(self.checker_id)
        return self._checker

    def delete(self) -> None:
        """
        Deletes the help request using the underlying HiveClient.

        Returns:
            None
        """
        self.hive_client.delete_help_request(self)


HelpLike = TypeVar("HelpLike", Help, int)
