"""Defines the Assignment type and related logic for representing student assignments in the Hive API."""

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Generator, Iterable, Self, TypeVar, cast

from attrs import define, field
from dateutil.parser import isoparse

from .common import UNSET, Unset
from .core_item import HiveCoreItem
from .enums.assignment_status_enum import AssignmentStatusEnum
from .notification_nested import NotificationNested

if TYPE_CHECKING:
    from ...client import HiveClient
    from .assignment_response import AssignmentResponse
    from .exercise import Exercise
    from .user import User

T = TypeVar("T", bound="Assignment")


@define
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

    hive_client: "HiveClient"
    id: int
    user_id: int
    checker_id: None | int
    checker_first_name: str
    checker_last_name: str
    is_subscribed: bool
    exercise_id: int
    assignment_status: AssignmentStatusEnum
    patbas: bool
    notifications: list["NotificationNested"]
    last_staff_updated: datetime.datetime
    work_time: int
    student_assignment_status: Unset | AssignmentStatusEnum = UNSET
    description: None | Unset | str = UNSET
    submission_count: Unset | int = UNSET
    total_check_count: Unset | int = UNSET
    manual_check_count: Unset | int = UNSET
    flagged: Unset | bool = UNSET
    timer: None | Unset | str = UNSET

    # Lazy-loaded objects
    _user: "User | None" = field(init=False, default=None)
    _checker: "User | None" = field(init=False, default=None)
    _exercise: "Exercise | None" = field(init=False, default=None)

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

    def to_dict(self) -> dict[str, Any]:
        """Serialize Assignment to a dictionary."""
        result: dict[str, None | str | int | list[dict[str, Any]]] = {
            "id": self.id,
            "user": self.user_id,
            "checker": self.checker_id,
            "checker_first_name": self.checker_first_name,
            "checker_last_name": self.checker_last_name,
            "is_subscribed": self.is_subscribed,
            "exercise": self.exercise_id,
            "assignment_status": self.assignment_status.value,
            "patbas": self.patbas,
            "notifications": [n.to_dict() for n in self.notifications],
            "last_staff_updated": self.last_staff_updated.isoformat(),
            "work_time": self.work_time,
        }

        # Conditionally include optional/unset fields
        if not isinstance(self.student_assignment_status, Unset):
            result["student_assignment_status"] = self.student_assignment_status.value
        if not isinstance(self.description, Unset):
            result["description"] = self.description
        if not isinstance(self.submission_count, Unset):
            result["submission_count"] = self.submission_count
        if not isinstance(self.total_check_count, Unset):
            result["total_check_count"] = self.total_check_count
        if not isinstance(self.manual_check_count, Unset):
            result["manual_check_count"] = self.manual_check_count
        if not isinstance(self.flagged, Unset):
            result["flagged"] = self.flagged
        if not isinstance(self.timer, Unset):
            result["timer"] = self.timer

        return result

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any], hive_client: "HiveClient") -> Self:
        """Deserialize Assignment from a dictionary."""

        d = dict(src_dict)

        notifications = [
            NotificationNested.from_dict(
                cast(dict[str, Any], n), hive_client=hive_client
            )
            for n in d.pop("notifications", [])
        ]

        student_assignment_status = (
            AssignmentStatusEnum(d["student_assignment_status"])
            if "student_assignment_status" in d
            and not (
                isinstance(d["student_assignment_status"], Unset)
                or d["student_assignment_status"] is None
            )
            else UNSET
        )

        description = d.pop("description", UNSET)
        submission_count = d.pop("submission_count", UNSET)
        total_check_count = d.pop("total_check_count", UNSET)
        manual_check_count = d.pop("manual_check_count", UNSET)
        flagged = d.pop("flagged", UNSET)
        timer = d.pop("timer", UNSET)

        return cls(
            hive_client=hive_client,
            id=d["id"],
            user_id=d["user"],
            checker_id=cast("int | None", d["checker"]),
            checker_first_name=d["checker_first_name"],
            checker_last_name=d["checker_last_name"],
            is_subscribed=d["is_subscribed"],
            exercise_id=d["exercise"],
            assignment_status=AssignmentStatusEnum(d["assignment_status"]),
            patbas=d["patbas"],
            notifications=notifications,
            last_staff_updated=isoparse(d["last_staff_updated"]),
            work_time=d["work_time"],
            student_assignment_status=student_assignment_status,
            description=cast("str | None | Unset", description),
            submission_count=cast("int | Unset", submission_count),
            total_check_count=cast("int | Unset", total_check_count),
            manual_check_count=cast("int | Unset", manual_check_count),
            flagged=cast("bool | Unset", flagged),
            timer=cast("str | None | Unset", timer),
        )

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
        if self.user.number is None or isinstance(self.user.number, Unset):
            return NotImplemented
        if value.user.number is None or isinstance(value.user.number, Unset):
            return NotImplemented
        return self.user.number < value.user.number

    def get_responses(self) -> Iterable["AssignmentResponse"]:
        """Fetch all responses to this assignment.
        Responses include both student and mentor submissions, comments, WIP, ..."""
        return self.hive_client.get_assignment_responses(assignment=self.id)

    def __iter__(self) -> Generator["AssignmentResponse", None, None]:
        """Allow iteration over this Assignment to yield its responses."""
        yield from self.get_responses()


AssignmentLike = Assignment | int
