"""A single item in a learning queue, either referencing an exercise or another queue."""

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self, TypeVar, Union

from attrs import define

from .common import UNSET, Unset
from .core_item import HiveCoreItem
from .enums.queue_rule_enum import QueueRuleEnum

if TYPE_CHECKING:
    from ...client import HiveClient
    from .exercise import Exercise
    from .queue import Queue

T = TypeVar("T", bound="QueueItem")


@define
class QueueItem(HiveCoreItem):
    """A single item in a learning queue, either referencing an exercise or another queue."""

    hive_client: "HiveClient"
    id: int
    order: int
    exercise: Union["Exercise", None]
    nested_queue: Union["Queue", None]
    queue_rule: QueueRuleEnum
    enabled: bool
    continue_on_redo: Unset | bool = UNSET

    def to_dict(self) -> dict[str, Any]:
        from .exercise import Exercise  # pylint: disable=import-outside-toplevel
        from .queue import Queue  # pylint: disable=import-outside-toplevel

        return {
            "id": self.id,
            "order": self.order,
            "exercise": (
                self.exercise.to_dict()
                if isinstance(self.exercise, Exercise)
                else self.exercise
            ),
            "nested_queue": (
                self.nested_queue.to_dict()
                if isinstance(self.nested_queue, Queue)
                else self.nested_queue
            ),
            "queue_rule": self.queue_rule.value,
            "enabled": self.enabled,
            **(
                {"continue_on_redo": self.continue_on_redo}
                if self.continue_on_redo is not UNSET
                else {}
            ),
        }

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any], hive_client: "HiveClient") -> Self:
        from .exercise import Exercise  # pylint: disable=import-outside-toplevel
        from .queue import Queue  # pylint: disable=import-outside-toplevel

        d = dict(src_dict)

        def _parse_exercise(data: dict[str, Any] | None) -> Union["Exercise", None]:
            if data is None:
                return data
            return Exercise.from_dict(data, hive_client=hive_client)

        def _parse_nested_queue(data: dict[str, Any] | None) -> Union["Queue", None]:
            if data is None:
                return data
            return Queue.from_dict(data, hive_client=hive_client)

        return cls(
            hive_client=hive_client,
            id=d.pop("id"),
            order=d.pop("order"),
            exercise=_parse_exercise(d.pop("exercise")),
            nested_queue=_parse_nested_queue(d.pop("nested_queue")),
            queue_rule=QueueRuleEnum(d.pop("queue_rule")),
            enabled=d.pop("enabled"),
            continue_on_redo=d.pop("continue_on_redo", UNSET),
        )
