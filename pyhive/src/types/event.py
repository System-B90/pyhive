"""
Name: event.py
Purpose: Model definition for calendar events in the Hive system.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

import datetime
from typing import TYPE_CHECKING, Annotated, Any, TypeVar

from typing_extensions import Self

from pydantic import Field

from .core_item import HiveCoreItem
from .enums.event_type_enum import EventTypeEnum

if TYPE_CHECKING:
    from ...client import HiveClient
    from .event_attendees_type_0_item import EventAttendeesType0Item


class Event(HiveCoreItem):
    """Calendar event model.

    Attributes:
        start: Event start datetime (ISO 8601).
        end: Event end datetime.
        title: Optional title.
        attendees: Optional list of attendees.
        subject_id: Optional related subject ID.
        subject_name: Optional subject display name.
        color: Optional display color for UI.
        type_: Event type (e.g. Patbas, Lecture).
        module_id: Optional associated module ID.
        lesson_name: Optional lesson name.
        location: Optional physical or virtual location.

    """

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]
    start: datetime.datetime
    end: datetime.datetime
    title: str | None
    attendees: "list[EventAttendeesType0Item] | None"
    subject_id: int | None
    subject_name: str | None
    color: str | None
    type_: EventTypeEnum = Field(alias="type")
    module_id: int | None
    lesson_name: str | None
    location: str | None = Field(default=None)

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Event):
            return False
        return (
            self.start == value.start
            and self.end == value.end
            and self.title == value.title
            and self.attendees == value.attendees
            and self.subject_id == value.subject_id
            and self.subject_name == value.subject_name
            and self.color == value.color
            and self.type_ == value.type_
            and self.module_id == value.module_id
            and self.lesson_name == value.lesson_name
            and self.location == value.location
        )


T = TypeVar("T", bound="Event")
