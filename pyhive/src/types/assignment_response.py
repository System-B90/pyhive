"""
Name: assignment_response.py
Purpose: Responses to assignments given to students.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from collections.abc import Generator
from typing import TYPE_CHECKING, Annotated, Any, Self, TypeVar

from pydantic import Field, PrivateAttr

from ._generated.models import AssignmentResponse as _AssignmentResponseBase
from .assignment_response_content import AssignmentResponseContent
from .autocheck_status import AutoCheckStatus

if TYPE_CHECKING:
    from ...client import HiveClient
    from .assignment import Assignment
    from .user import User


class AssignmentResponse(_AssignmentResponseBase):
    """A response to an assignment.

    Scalar fields are inherited from the generated base. ``contents`` and
    ``autocheck_statuses`` are overridden to PyHive's curated nested types, and
    ``assignment_id`` is an injected (non-spec) field carrying parent context.
    """

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]
    assignment_id: int = Field(exclude=True)
    contents: list[AssignmentResponseContent]
    autocheck_statuses: list[AutoCheckStatus] | None = Field(default=None)
    dear_student: bool | None = Field(default=True)

    _user: "User | None" = PrivateAttr(default=None)
    _assignment: "Assignment | None" = PrivateAttr(default=None)

    @classmethod
    def from_dict(
        cls,
        src_dict: dict[str, Any],
        assignment_id: int,
        hive_client: "HiveClient",
    ) -> Self:
        """
        Deserializes an AssignmentResponse instance from a dictionary payload.

        Args:
            src_dict (dict[str, Any]): The raw dictionary from the API response.
            assignment_id (int): The ID of the parent assignment.
            hive_client (HiveClient): The client instance for deferred network operations.

        Returns:
            Self: An instantiated and validated AssignmentResponse model.
        """
        data = dict(src_dict)
        data["hive_client"] = hive_client
        data["assignment_id"] = assignment_id
        return cls.model_validate(data)

    @property
    def user(self) -> "User":
        """
        Lazily loads and returns the user this assignment belongs to.

        Returns:
            User: The associated user entity.
        """
        if self._user is None:
            self._user = self.hive_client.get_user(self.user_id)
        return self._user

    @property
    def assignment(self) -> "Assignment":
        """
        Lazily loads and returns the assignment this response belongs to.

        Returns:
            Assignment: The associated assignment entity.
        """
        if self._assignment is None:
            self._assignment = self.hive_client.get_assignment(
                assignment_id=self.assignment_id
            )
        return self._assignment

    def iter_contents(self) -> Generator[AssignmentResponseContent, None, None]:
        """
        Allows iteration over this AssignmentResponse to yield its contents.

        Yields:
            Generator[AssignmentResponseContent, None, None]: A generator producing content parts.
        """
        yield from self.contents


AssignmentResponseLike = TypeVar("AssignmentResponseLike", AssignmentResponse, int)
