"""
Name: event_attendee.py
Purpose: Model linking a schedule event to an attending class.
Created: 2026-08-23
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Annotated, Any, TypeVar
from uuid import UUID

from pydantic import Field
from typing_extensions import Self

from ._generated.models import EventAttendee as _EventAttendeeBase

if TYPE_CHECKING:
    from ...client import HiveClient
    from .class_ import Class


class EventAttendee(_EventAttendeeBase):
    """Links a schedule event (``event_id``) to an attending class (``attendee_class_id``)."""

    # Hive < 7.3.0 serves integer ids here; 7.3.0+ serves UUIDs.
    id: UUID | int | None = None  # type: ignore[assignment]
    event_id: UUID | int  # type: ignore[assignment]

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)

    @property
    def attendee_class(self) -> "Class":
        """Lazily load and return the attending class."""
        return self.hive_client.get_class(self.attendee_class_id)


T = TypeVar("T", bound="EventAttendee")
