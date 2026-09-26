"""
Name: event_category.py
Purpose: Model for schedule event categories in the Hive system.
Created: 2026-08-23
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Annotated, Any, TypeVar

from pydantic import Field
from typing_extensions import Self

from ._generated.models import EventCategory as _EventCategoryBase

if TYPE_CHECKING:
    from ...client import HiveClient


class EventCategory(_EventCategoryBase):
    """A schedule event category (name, color, visibility flags). Data fields are inherited."""

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)


T = TypeVar("T", bound="EventCategory")
