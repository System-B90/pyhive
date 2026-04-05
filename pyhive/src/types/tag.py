"""
Name: tag.py
Purpose: Module defining the Tag class for Hive tags.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Any, Self, TypeVar

from pydantic import Field

from .core_item import HiveCoreItem

if TYPE_CHECKING:
    from ...client import HiveClient


class Tag(HiveCoreItem):
    """Attributes:
    id (int):
    name (str):
    color (str):

    """

    hive_client: "HiveClient" = Field(exclude=True, repr=False)
    id: int
    name: str
    color: str

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)


T = TypeVar("T", bound="Tag")
