"""
Name: me.py
Purpose: Model for the authenticated user's own profile ("me") in Hive.
Created: 2026-08-23
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Annotated, Any, Self, TypeVar

from pydantic import Field

from ._generated.models import Me as _MeBase

if TYPE_CHECKING:
    from ...client import HiveClient


class Me(_MeBase):
    """The authenticated user's own profile. Data fields are inherited."""

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)


T = TypeVar("T", bound="Me")
