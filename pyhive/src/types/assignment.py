"""
Name: assignment.py
Purpose: Defines the Assignment type and related logic for representing student assignments in the Hive API.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

import datetime
from typing import TYPE_CHECKING, Any, Generator, Iterable, Self, TypeVar

from pydantic import Field, PrivateAttr

from .core_item import HiveCoreItem
from .enums.assignment_status_enum import AssignmentStatusEnum
from .notification_nested import NotificationNested

if TYPE_CHECKING:
    from ...client import HiveClient
    from .assignment_response import AssignmentResponse
    from .exercise import Exercise
    from .user import User


class Assignment(HiveCoreItem):
    """Represents a student's assignment for an exercise.

    Attributes:
        hive_client: Reference to the Hive API client.
        id: Unique assignment ID.
        user_id: ID of the assigned student.
        checker_id: ID of the assigned checker, or None.
        checker_first_name: First name of the checker.
        checker_last_name: Last name of the checker.
        is_subscribed: Whether the student is subscribed to updates.
        exercise_id: ID of the exercise.
        assignment_status: Current state of the assignment.
        patbas: Whether it's a PATBAS assignment.
        notifications: List of related notifications.
        last_staff_updated: Timestamp of the last staff update.
        work_time: Total work time in minutes.
        student_assignment_status: The student's view of the assignment status.
        description: Optional text description.
        submission_count: Total number of submissions.
        total_check_count: Number of total checks.
        manual_check_count: Number of manual checks.
        flagged: Whether the assignment is flagged for review.
        timer: Optional timer state string.

    """

    hive_client: "HiveClient" = Field(exclude=True, repr=False)
    id: int
    user_id: int = Field(alias="user")
    checker_id: int | None = Field(alias="checker")
    checker_first_name: str
    checker_last_name: str
    is_subscribed: bool
    exercise_id: int = Field(alias="exercise")
    assignment_status: AssignmentStatusEnum
    patbas: bool
    notifications: list["NotificationNested"]
    last_staff_updated: datetime.datetime
    work_time: int
    student_assignment_status: AssignmentStatusEnum | None = Field(default=None)
    description: str | None = Field(default=None)
    submission_count: int | None = Field(default=None)
    total_check_count: int | None = Field(default=None)
    manual_check_count: int | None = Field(default=None)
    flagged: bool | None = Field(default=None)
    timer: str | None = Field(default=None)

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

    def __iter__(self) -> Generator["AssignmentResponse", None, None]:
        """Allow iteration over this Assignment to yield its responses."""
        yield from self.get_responses()


T = TypeVar("T", bound="Assignment")
AssignmentLike = Assignment | int
