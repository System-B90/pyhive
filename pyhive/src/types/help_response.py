"""
Name: help_response.py
Purpose: Model definition for help responses in the Hive system.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Annotated, Any, TypeVar

from pydantic import Field, PrivateAttr
from typing_extensions import Self

from ._generated.models import HelpResponse as _HelpResponseBase

if TYPE_CHECKING:
    from ...client import HiveClient
    from .user import User


class HelpResponse(_HelpResponseBase):
    """A response to a help request. Data fields are inherited from the generated
    base; ``dear_student`` keeps PyHive's ``True`` default."""

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]
    dear_student: bool = Field(default=True)

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
