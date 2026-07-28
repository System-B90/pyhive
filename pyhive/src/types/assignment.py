"""
Name: assignment.py
Purpose: Defines the Assignment type and related logic for representing student assignments in the Hive API.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from collections.abc import Iterable
from typing import TYPE_CHECKING, Annotated, Any, Self, TypeVar

from pydantic import Field, PrivateAttr

from ._generated.models import Assignment as _AssignmentBase
from .notification_nested import NotificationNested

if TYPE_CHECKING:
    from ...client import HiveClient
    from .assignment_response import AssignmentResponse
    from .exercise import Exercise
    from .user import User


class Assignment(_AssignmentBase):
    """Represents a student's assignment for an exercise.

    Scalar and FK fields are inherited from the generated base. The nested
    ``notifications`` field is overridden to use PyHive's curated
    ``NotificationNested`` (with its lazy ``from_user`` relation).
    """

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]
    notifications: list["NotificationNested"]

    # Lazy-loaded objects
    _user: "User | None" = PrivateAttr(default=None)
    _checker: "User | None" = PrivateAttr(default=None)
    _exercise: "Exercise | None" = PrivateAttr(default=None)

    @property
    def user(self) -> "User":
        """Lazily load and return the user this assignment belongs to."""
        if self._user is None:
            self._user = self.hive_client.get_user(self.user_id)
        return self._user

    @property
    def checker(self) -> "User | None":
        """Lazily load and return the checker (if any) assigned to this assignment."""
        if self.checker_id is None:
            return None
        if self._checker is None:
            self._checker = self.hive_client.get_user(self.checker_id)
        return self._checker

    @property
    def exercise(self) -> "Exercise":
        """Lazily load and return the exercise associated with this assignment."""
        if self._exercise is None:
            self._exercise = self.hive_client.get_exercise(self.exercise_id)
        return self._exercise

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Assignment):
            return False
        return (
            self.id == value.id
            and self.exercise_id == value.exercise_id
            and self.user_id == value.user_id
            and self.checker_id == value.checker_id
            and self.assignment_status == value.assignment_status
            and self.exercise == value.exercise
        )

    def __lt__(self, value: object) -> bool:
        if not isinstance(value, Assignment):
            return NotImplemented
        if self.user.number is None:
            return NotImplemented
        if value.user.number is None:
            return NotImplemented
        return self.user.number < value.user.number

    def get_responses(self) -> Iterable["AssignmentResponse"]:
        """Fetch all responses to this assignment.
        Responses include both student and mentor submissions, comments, WIP, ..."""
        return self.hive_client.get_assignment_responses(assignment=self.id)


T = TypeVar("T", bound="Assignment")
AssignmentLike = Assignment | int
