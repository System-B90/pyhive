"""
Name: help_.py
Purpose: Model for student help requests.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Any, Self, TypeVar

from pydantic import Field, PrivateAttr

from .core_item import HiveCoreItem
from .enums.help_status_enum import HelpStatusEnum
from .enums.help_type_enum import HelpTypeEnum
from .enums.visibility_enum import VisibilityEnum

if TYPE_CHECKING:
    from ...client import HiveClient
    from .exercise import Exercise
    from .help_response_segel_nested import HelpResponseSegelNested
    from .notification_nested import NotificationNested
    from .user import User


class Help(HiveCoreItem):
    """
    A student's help request.

    Attributes:
        id: Unique identifier.
        user_id: ID of the user requesting help.
        checker_id: ID of the assigned checker, if any.
        checker_first_name: First name of the checker.
        checker_last_name: Last name of the checker.
        is_subscribed: Whether the user is subscribed to updates.
        help_type: Categorical type of the request.
        help_status: Current resolution status.
        for_exercise_id: ID of the associated exercise, if any.
        responses: List of nested response objects.
        notifications: List of nested notification objects.
        title: Optional title of the request.
        visibility: Optional visibility restriction.
    """

    hive_client: "HiveClient" = Field(exclude=True, repr=False)
    id: int
    user_id: int = Field(alias="user")
    checker_id: int | None = Field(default=None, alias="checker")
    checker_first_name: str | None = Field(default=None)
    checker_last_name: str | None = Field(default=None)
    is_subscribed: bool
    help_type: HelpTypeEnum
    help_status: HelpStatusEnum
    for_exercise_id: int | None = Field(default=None, alias="for_exercise")
    responses: list["HelpResponseSegelNested"]
    notifications: list["NotificationNested"]

    title: str | None = Field(default=None)
    visibility: VisibilityEnum | None = Field(default=None)

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
