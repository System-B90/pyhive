"""
Name: schedule_event.py
Purpose: Model for calendar events served by the Hive schedule API.
Created: 2026-08-23
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Annotated, Any, TypeVar
from uuid import UUID

from pydantic import Field
from typing_extensions import Self

from ._generated.models import Event as _ScheduleEventBase

if TYPE_CHECKING:
    from ...client import HiveClient


class ScheduleEvent(_ScheduleEventBase):
    """A calendar event (category/room/lesson links, attendees). Data fields are inherited."""

    # Hive < 7.3.0 serves integer ids here; 7.3.0+ serves UUIDs.
    id: UUID | int | None = None  # type: ignore[assignment]
    category_id: UUID | int | None = None  # type: ignore[assignment]
    lesson_id: UUID | int | None = None  # type: ignore[assignment]

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)


T = TypeVar("T", bound="ScheduleEvent")
