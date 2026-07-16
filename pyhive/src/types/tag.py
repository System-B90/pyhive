"""
Name: tag.py
Purpose: Module defining the Tag class for Hive tags.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Annotated, Any, Self, TypeVar

from pydantic import Field

from ._generated.models import Tag as _TagBase

if TYPE_CHECKING:
    from ...client import HiveClient


class Tag(_TagBase):
    """A Hive tag (id, name, color). Data fields are inherited from the generated base."""

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)


T = TypeVar("T", bound="Tag")
