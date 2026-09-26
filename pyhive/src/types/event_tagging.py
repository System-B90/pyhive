"""
Name: event_tagging.py
Purpose: Model linking a schedule event to an event tag.
Created: 2026-08-23
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Annotated, Any, TypeVar
from uuid import UUID

from pydantic import Field
from typing_extensions import Self

from ._generated.models import EventTagging as _EventTaggingBase

if TYPE_CHECKING:
    from ...client import HiveClient
    from .event_tag import EventTag


class EventTagging(_EventTaggingBase):
    """Links a schedule event (``event_id``) to an event tag (``tag_id``)."""

    # Hive < 7.3.0 serves integer ids here; 7.3.0+ serves UUIDs.
    id: UUID | int | None = None  # type: ignore[assignment]
    event_id: UUID | int  # type: ignore[assignment]
    tag_id: UUID | int  # type: ignore[assignment]

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)

    @property
    def tag(self) -> "EventTag":
        """Lazily load and return the tagged event tag."""
        return self.hive_client.get_event_tag(self.tag_id)


T = TypeVar("T", bound="EventTagging")
