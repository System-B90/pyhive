"""
Name: event_attendees_type_0_item.py
Purpose: EventAttendeesType0Item type class
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Annotated, Any, TypeVar

from typing_extensions import Self

from pydantic import Field

from .core_item import HiveCoreItem

if TYPE_CHECKING:
    from ...client import HiveClient


class EventAttendeesType0Item(HiveCoreItem):
    """Attributes:
    name (str):
    id (int):
    description (str | None):

    """

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]
    name: str
    id: int
    description: str | None = Field(default=None)

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, EventAttendeesType0Item):
            return False
        return self.id == value.id


T = TypeVar("T", bound="EventAttendeesType0Item")
