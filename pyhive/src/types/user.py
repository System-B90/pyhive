"""
Name: user.py
Purpose: Hive management course user type.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from collections.abc import Iterable
from typing import TYPE_CHECKING, Annotated, Any, Self, TypeVar

from pydantic import Field, PrivateAttr

from ._generated.models import CourseUser as _UserBase

if TYPE_CHECKING:
    from ...client import HiveClient
    from .assignment import Assignment
    from .class_ import Class
    from .program import Program
    from .queue import Queue, QueueLike


class User(_UserBase):
    """Hive management course user. Data fields are inherited from the generated
    ``CourseUser`` base; this layer adds lazy relations and helpers."""

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]

    _current_assignment: "Assignment | None" = PrivateAttr(default=None)
    _mentees: "list[User] | None" = PrivateAttr(default=None)
    _program: "Program | None" = PrivateAttr(default=None)
    _mentor: "User | None" = PrivateAttr(default=None)
    _classes: "list[Class] | None" = PrivateAttr(default=None)
    _queue: "Queue | None" = PrivateAttr(default=None)
    _user_queue: "Queue | None" = PrivateAttr(default=None)
    _override_queue: "Queue | None" = PrivateAttr(default=None)

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        """Deserialize a User instance from a mapping."""
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)

    @property
    def program(self) -> "Program | None":
        """The program this user is in."""
        if not isinstance(self.program_id, int):
            return None
        if self._program is None:
            self._program = self.hive_client.get_program(self.program_id)
        return self._program

    @property
    def mentees(self) -> list["User"]:
        """The mentees of this user."""
        if self._mentees is None:
            self._mentees = list(self.hive_client.get_users(id__in=self.mentee_ids))
        return self._mentees

    @property
    def mentor(self) -> "User | None":
        """The mentor of this user."""
        if not isinstance(self.mentor_id, int):
            return None
        if self._mentor is None:
            self._mentor = self.hive_client.get_user(self.mentor_id)
        return self._mentor

    @property
    def classes(self) -> list["Class"]:
        """The classes this user is in."""
        if self._classes is None:
            if self.class_ids is None:
                self._classes = []
            else:
                self._classes = list(
                    self.hive_client.get_classes(id__in=self.class_ids)
                )
        return self._classes

    @property
    def queue(self) -> "Queue | None":
        """The queue this user is in."""
        if not isinstance(self.queue_id, int):
            return None
        if self._queue is None:
            self._queue = self.hive_client.get_queue(self.queue_id)
        return self._queue

    @property
    def user_queue(self) -> "Queue | None":
        """The user queue this user is in."""
        if not isinstance(self.user_queue_id, int):
            return None
        if self._user_queue is None:
            self._user_queue = self.hive_client.get_queue(self.user_queue_id)
        return self._user_queue

    @property
    def override_queue(self) -> "Queue | None":
        """The override queue this user is in."""
        if not isinstance(self.override_queue_id, int):
            return None
        if self._override_queue is None:
            self._override_queue = self.hive_client.get_queue(self.override_queue_id)
        return self._override_queue

    @property
    def current_assignment(self) -> "Assignment | None":
        """The current assignment of this user."""
        if not isinstance(self.current_assignment_id, int):
            return None
        if self._current_assignment is None:
            self._current_assignment = self.hive_client.get_assignment(
                self.current_assignment_id
            )
        return self._current_assignment

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return False
        return self.id == other.id

    def get_assignments(self) -> Iterable["Assignment"]:
        """Get all assignments for this user."""
        return self.hive_client.get_assignments(for_user=self)

    def delete(self) -> None:
        self.hive_client.delete_user(self.id)

    def update(self) -> None:
        """Commit the current state of the user to the server"""
        assert self.hive_client.update_user(self) == self

    def set_queue(self, queue: "QueueLike") -> None:
        self.hive_client.set_users_queue(self, queue)


T = TypeVar("T", bound="User")
UserLike = TypeVar("UserLike", User, int)
