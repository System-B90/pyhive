"""
Name: lesson_rule.py
Purpose: Model for lesson queue rules in the Hive schedule.
Created: 2026-08-23
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Annotated, Any, TypeVar
from uuid import UUID

from pydantic import Field, PrivateAttr
from typing_extensions import Self

from ._generated.models import LessonRule as _LessonRuleBase

if TYPE_CHECKING:
    from ...client import HiveClient
    from .queue import Queue


class LessonRule(_LessonRuleBase):
    """A queue rule attached to a lesson. Data fields are inherited."""

    # Hive < 7.3.0 serves integer ids here; 7.3.0+ serves UUIDs.
    id: UUID | int  # type: ignore[assignment]
    parent_rule: UUID | int | None = None  # type: ignore[assignment]

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]

    _queue: "Queue | None" = PrivateAttr(default=None)

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)

    @property
    def queue(self) -> "Queue | None":
        """Lazily load and return the queue this rule points at (None if unset)."""
        if self._queue is None and self.queue_id is not None:
            self._queue = self.hive_client.get_queue(self.queue_id)
        return self._queue


T = TypeVar("T", bound="LessonRule")
