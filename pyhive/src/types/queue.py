"""
Name: queue.py
Purpose: Queue model for the Hive API (auto-generated).
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Any, Self, TypeVar

from pydantic import Field, PrivateAttr

from .core_item import HiveCoreItem

if TYPE_CHECKING:
    from ...client import HiveClient
    from .module import Module
    from .program import Program
    from .subject import Subject
    from .user import User


class Queue(HiveCoreItem):
    """Queue model representing a student/program/module queue entry.

    Attributes mirror the API JSON keys; relationship properties (``user``,
    ``module``, ``subject``, ``program``) lazily load the referenced
    objects using the supplied ``hive_client``.
    """

    hive_client: "HiveClient" = Field(exclude=True, repr=False)
    id: int
    name: str
    user_name: str | None
    subject_id: int | None
    subject_name: str | None
    subject_color: str | None
    subject_symbol: str | None
    module_name: str | None
    module_order: str | None
    program_id: int
    program_name: str
    description: str | None = Field(default=None)
    module_id: int | None = Field(default=None)
    user_id: int | None = Field(default=None)

    _user: "User | None" = PrivateAttr(default=None)
    _module: "Module | None" = PrivateAttr(default=None)
    _subject: "Subject | None" = PrivateAttr(default=None)
    _program: "Program | None" = PrivateAttr(default=None)

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        """Create a :class:`Queue` instance from a mapping (typically parsed JSON).

        Args:
            src_dict: Mapping with keys matching the API response.
            hive_client: Hive client used to lazily resolve relationships.

        Returns:
            A populated :class:`Queue` instance.
        """
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)

    @property
    def user(self) -> "User | None":
        """Lazily return the :class:`User` associated with this queue entry.

        Returns None when no user_id is set.
        """
        if self._user is None and isinstance(self.user_id, int):
            self._user = self.hive_client.get_user(self.user_id)
        return self._user

    @property
    def module(self) -> "Module | None":
        """Lazily return the :class:`Module` referenced by this queue entry.

        Returns None when no module_id is present.
        """
        if self._module is None and isinstance(self.module_id, int):
            self._module = self.hive_client.get_module(self.module_id)
        return self._module

    @property
    def subject(self) -> "Subject | None":
        """Return the resolved :class:`Subject` or None if not available."""
        if isinstance(self.subject_id, int):
            return self.hive_client.get_subject(self.subject_id)
        return None

    @property
    def program(self) -> "Program":
        """Return the resolved :class:`Program` for this queue entry."""
        return self.hive_client.get_program(self.program_id)

    def delete(self) -> None:
        self.hive_client.delete_queue(self.id)


T = TypeVar("T", bound="Queue")
QueueLike = TypeVar("QueueLike", Queue, int)
