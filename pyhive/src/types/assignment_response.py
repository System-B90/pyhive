"""
Name: assignment_response.py
Purpose: Responses to assignments given to students.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

import datetime
from collections.abc import Generator
from typing import TYPE_CHECKING, Any, Self, TypeVar

from pydantic import Field, PrivateAttr

from .assignment_response_content import AssignmentResponseContent
from .autocheck_status import AutoCheckStatus
from .core_item import HiveCoreItem
from .enums.assignment_response_type_enum import AssignmentResponseTypeEnum

if TYPE_CHECKING:
    from ...client import HiveClient
    from .assignment import Assignment
    from .user import User


class AssignmentResponse(HiveCoreItem):
    """
    Attributes:
        id (int): Unique identifier.
        user_id (int): ID of the user submitting the response.
        contents (list[AssignmentResponseContent]): List of content parts.
        date (datetime.datetime): Timestamp of the response.
        response_type (AssignmentResponseTypeEnum): Type of response (e.g., Submission, Comment).
        autocheck_statuses (list[AutoCheckStatus] | None): Optional autocheck evaluations.
        file_name (str | None): Optional file name for attachments.
        dear_student (bool | None): Flag for salutation inclusion. Default: True.
        hide_checker_name (bool | None): Flag to anonymize the checker.
        segel_only (bool | None): Flag to restrict visibility to staff.
    """

    hive_client: "HiveClient" = Field(exclude=True, repr=False)
    assignment_id: int = Field(exclude=True)
    id: int
    user_id: int = Field(alias="user")
    contents: list[AssignmentResponseContent]
    date: datetime.datetime
    response_type: AssignmentResponseTypeEnum

    autocheck_statuses: list[AutoCheckStatus] | None = Field(default=None)
    file_name: str | None = Field(default=None)
    dear_student: bool | None = Field(default=True)
    hide_checker_name: bool | None = Field(default=None)
    segel_only: bool | None = Field(default=None)

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
