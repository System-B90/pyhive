"""
Name: user.py
Purpose: Hive management course user type.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

import datetime
from typing import Annotated,TYPE_CHECKING, Any, Iterable, Self, TypeVar

from pydantic import Field, PrivateAttr

from .core_item import HiveCoreItem
from .enums.clearance_enum import ClearanceEnum
from .enums.gender_enum import GenderEnum
from .enums.status_enum import StatusEnum

if TYPE_CHECKING:
    from ...client import HiveClient
    from .assignment import Assignment
    from .class_ import Class
    from .program import Program
    from .queue import Queue, QueueLike


class User(HiveCoreItem):
    """Hive management course user.

    Attributes:
    id (int):
    display_name (str):
    clearance (ClearanceEnum):
        * `1` - Hanich
        * `2` - Checker
        * `3` - Segel
        * `5` - Admin
    gender (GenderEnum):
        * `Male` - Male
        * `Female` - Female
        * `NonBinary` - Nonbinary
    current_assignment (int | None):
    current_assignment_options (list[int]):
    mentee_ids (list[int]):
    username (str): Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.
    status (StatusEnum):
        * `Present` - Present
        * `Raised Hand` - Raisedhand
        * `Toilet Request` - Toiletrequest
        * `Toilet` - Toilet
        * `Personal Talk` - Personaltalk
        * `Work Talk` - Worktalk
        * `Medical` - Medical
        * `Prayer` - Prayer
        * `Room` - Room
        * `Home` - Home
    status_date (datetime.datetime):
    avatar_filename (str | None):
    number (int | None):
    program (int | None):
    checkers_brief (str | None):
    mentor (int | None):
    classes (list[int] | None):
    first_name (str | None):
    last_name (str | None):
    queue (int | None):
    disable_queue (bool | None):
    user_queue (int | None):
    disable_user_queue (bool | None):
    override_queue (int | None):
    confirmed (bool | None):
    teacher (bool | None):
    hostname (str | None):

    """

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]
    id: int
    display_name: str
    clearance: ClearanceEnum
    gender: GenderEnum
    current_assignment_id: int | None = Field(default=None, alias="current_assignment")
    _current_assignment: "Assignment | None" = PrivateAttr(default=None)
    current_assignment_options: list[int]
    mentee_ids: list[int] = Field(alias="mentees")
    _mentees: "list[User] | None" = PrivateAttr(default=None)
    username: str
    status: StatusEnum
    status_date: datetime.datetime
    avatar_filename: str | None = Field(default=None)
    number: int | None = Field(default=None)
    program_id: int | None = Field(default=None, alias="program")
    _program: "Program | None" = PrivateAttr(default=None)
    checkers_brief: str | None = Field(default=None)
    mentor_id: int | None = Field(default=None, alias="mentor")
    _mentor: "User | None" = PrivateAttr(default=None)
    class_ids: list[int] | None = Field(default=None, alias="classes")
    _classes: "list[Class] | None" = PrivateAttr(default=None)
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    queue_id: int | None = Field(default=None, alias="queue")
    _queue: "Queue | None" = PrivateAttr(default=None)
    disable_queue: bool | None = Field(default=None)
    user_queue_id: int | None = Field(default=None, alias="user_queue")
    _user_queue: "Queue | None" = PrivateAttr(default=None)
    disable_user_queue: bool | None = Field(default=None)
    override_queue_id: int | None = Field(default=None, alias="override_queue")
    _override_queue: "Queue | None" = PrivateAttr(default=None)
    confirmed: bool | None = Field(default=None)
    teacher: bool | None = Field(default=None)
    hostname: str | None = Field(default=None)

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

    def __eq__(self, other: Any) -> bool:
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
