"""Model definition for calendar events in the Hive system.

Represents a scheduled item such as a lecture, workshop, or PATBAS session,
including timing, participants, subject, and related module.
"""

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self, TypeVar, cast

from attrs import define
from dateutil.parser import isoparse

from .common import UNSET, Unset
from .core_item import HiveCoreItem
from .enums.event_type_enum import EventTypeEnum

if TYPE_CHECKING:
    from ...client import HiveClient
    from .event_attendees_type_0_item import EventAttendeesType0Item

T = TypeVar("T", bound="Event")


@define
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

    start: datetime.datetime
    end: datetime.datetime
    title: None | str
    attendees: None | list["EventAttendeesType0Item"]
    subject_id: None | int
    subject_name: None | str
    color: None | str
    type_: EventTypeEnum
    module_id: None | int
    lesson_name: None | str
    location: None | Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        start = self.start.isoformat()
        end = self.end.isoformat()

        attendees: None | list[dict[str, Any]]
        attendees = (
            [a.to_dict() for a in self.attendees]
            if isinstance(self.attendees, list)
            else self.attendees
        )

        location = UNSET if isinstance(self.location, Unset) else self.location

        field_dict: dict[str, Any] = {
            "start": start,
            "end": end,
            "title": self.title,
            "attendees": attendees,
            "subject_id": self.subject_id,
            "subject_name": self.subject_name,
            "color": self.color,
            "type": self.type_.value,
            "module_id": self.module_id,
            "lesson_name": self.lesson_name,
        }

        if location is not UNSET:
            field_dict["location"] = location

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any], hive_client: "HiveClient") -> Self:
        from .event_attendees_type_0_item import EventAttendeesType0Item  # pylint: disable=import-outside-toplevel

        d = dict(src_dict)

        def _parse_optional_str(data: object) -> None | str:
            return data if data is None else cast("str", data)

        def _parse_optional_int(data: object) -> None | int:
            return data if data is None else cast("int", data)

        def _parse_optional_list(data: object) -> None | list[EventAttendeesType0Item]:
            if data is None:
                return None
            if not isinstance(data, list):
                raise TypeError
            data_list = cast("list[object]", data)
            try:
                return [
                    EventAttendeesType0Item.from_dict(
                        cast(dict[str, Any], item),
                        hive_client=hive_client,
                    )
                    for item in data_list
                ]
            except Exception:  # pylint: disable=broad-except
                return cast("None | list[EventAttendeesType0Item]", data)

        def _parse_optional_unset_str(data: object) -> None | Unset | str:
            if data is None or isinstance(data, Unset):
                return data
            return cast("str", data)

        return cls(
            start=isoparse(d.pop("start")),
            end=isoparse(d.pop("end")),
            title=_parse_optional_str(d.pop("title")),
            attendees=_parse_optional_list(d.pop("attendees")),
            subject_id=_parse_optional_int(d.pop("subject_id")),
            subject_name=_parse_optional_str(d.pop("subject_name")),
            color=_parse_optional_str(d.pop("color")),
            type_=EventTypeEnum(d.pop("type")),
            module_id=_parse_optional_int(d.pop("module_id")),
            lesson_name=_parse_optional_str(d.pop("lesson_name")),
            location=_parse_optional_unset_str(d.pop("location", UNSET)),
        )

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
