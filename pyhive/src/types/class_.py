"""
Name: class_.py
Purpose: Defines the Class type representing a school class/group in a program.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Annotated, Any, TypeVar

from pydantic import Field, PrivateAttr
from typing_extensions import Self

from ._generated.models import Class as _ClassBase

if TYPE_CHECKING:
    from ...client import HiveClient
    from .program import Program
    from .user import User


class Class(_ClassBase):
    """Represents a school class/group in a program.

    Data fields are inherited from the generated base.
    """

    # Excluded from serialization, prevents network coupling in the data payload
    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]

    # Private attributes for internal lazy-loading state
    _program: "Program | None" = PrivateAttr(default=None)
    _users: "list[User] | None" = PrivateAttr(default=None)

    @property
    def program(self) -> "Program":
        """
        Lazily loads the associated Program object.

        Returns:
            Program: The program entity associated with this class.
        """
        if self._program is None:
            self._program = self.hive_client.get_program(self.program_id)
        return self._program

    @property
    def users(self) -> list["User"]:
        """
        Lazily loads the list of User objects in this class.

        Returns:
            list[User]: The list of user entities assigned to this class.
        """
        if self._users is None:
            self._users = [self.hive_client.get_user(uid) for uid in self.user_ids]
        return self._users

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        """
        Deserializes a Class instance from a dictionary payload.

        Args:
            src_dict (dict[str, Any]): The raw dictionary from the API response.
            hive_client (HiveClient): The client instance for deferred network operations.

        Returns:
            Self: An instantiated and validated Class model.
        """
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)

    def delete(self) -> None:
        """
        Deletes the class using the underlying HiveClient.

        Returns:
            None
        """
        self.hive_client.delete_class(self)

    def update(self) -> None:
        """
        Updates the class using the underlying HiveClient.

        Returns:
            None
        """
        self.hive_client.update_class(self)


ClassLike = TypeVar("ClassLike", Class, int)
