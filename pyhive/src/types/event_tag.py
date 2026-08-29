"""
Name: event_tag.py
Purpose: Model for schedule event tags in the Hive system.
Created: 2026-08-23
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Annotated, Any, Self, TypeVar

from pydantic import Field

from ._generated.models import EventTag as _EventTagBase

if TYPE_CHECKING:
    from ...client import HiveClient


class EventTag(_EventTagBase):
    """A schedule event tag (id, name, color). Data fields are inherited."""

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)


T = TypeVar("T", bound="EventTag")
