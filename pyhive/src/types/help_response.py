"""
Name: help_response.py
Purpose: Model definition for help responses in the Hive system.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

import datetime
from typing import Annotated,TYPE_CHECKING, Any, Self, TypeVar

from pydantic import Field, PrivateAttr

from .core_item import HiveCoreItem
from .enums.help_response_type_enum import HelpResponseTypeEnum

if TYPE_CHECKING:
    from ...client import HiveClient
    from .user import User


class HelpResponse(HiveCoreItem):
    """A response to a help request.

    Attributes:
        id: Unique identifier for the response.
        user: ID of the responding user.
        date: Timestamp of the response.
        response_type: Type of the response (e.g., Resolve, Open, Comment).
        contents: Optional text content of the response.
        file_name: Optional name of an attached file.
        dear_student: Whether to include a "Dear student" greeting. Default is True.
        hide_checker_name: If True, the name of the checker is hidden.
        segel_only: If True, the response is visible only to staff.

    """

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]
    id: int
    user_id: int = Field(alias="user")
    date: datetime.datetime
    response_type: HelpResponseTypeEnum
    contents: str | None = Field(default=None)
    file_name: str | None = Field(default=None)
    dear_student: bool = Field(default=True)
    hide_checker_name: bool | None = Field(default=None)
    segel_only: bool | None = Field(default=None)

    # Lazy-loaded objects
    _user: "User | None" = PrivateAttr(default=None)

    @property
    def user(self) -> "User":
        """Returns the User object associated with this instance.

        If the User object has not been retrieved yet,
         it fetches the user using the hive_client and caches it for future calls.

        Returns:
            User: The user associated with this instance.

        """
        if self._user is None:
            self._user = self.hive_client.get_user(self.user_id)
        return self._user

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)


T = TypeVar("T", bound="HelpResponse")
