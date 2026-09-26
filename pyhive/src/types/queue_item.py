"""
Name: queue_item.py
Purpose: A single item in a learning queue, either referencing an exercise or another queue.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Any, TypeVar

from typing_extensions import Self

from pydantic import Field

from .core_item import HiveCoreItem
from .enums.queue_rule_enum import QueueRuleEnum

if TYPE_CHECKING:
    from ...client import HiveClient
    from .exercise import Exercise
    from .queue import Queue


class QueueItem(HiveCoreItem):
    """A single item in a learning queue, either referencing an exercise or another queue."""

    hive_client: Any = Field(exclude=True, repr=False)
    id: int
    order: int
    exercise: "Exercise | None"
    nested_queue: "Queue | None"
    queue_rule: QueueRuleEnum
    enabled: bool
    continue_on_redo: bool | None = Field(default=None)

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)


T = TypeVar("T", bound="QueueItem")
