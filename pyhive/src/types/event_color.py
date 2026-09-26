"""
Name: event_color.py
Purpose: Module for EventColor type.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Annotated, Any, TypeVar

from pydantic import Field
from typing_extensions import Self

from .core_item import HiveCoreItem

if TYPE_CHECKING:
    from ...client import HiveClient


class EventColor(HiveCoreItem):
    """Attributes:
    id (int):
    name (str):
    color (str):

    """

    id: int
    name: str
    color: str
    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)


T = TypeVar("T", bound="EventColor")
