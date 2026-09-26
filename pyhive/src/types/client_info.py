"""
Name: client_info.py
Purpose: Model for public SSO client metadata exposed by Hive.
Created: 2026-08-23
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Annotated, Any, TypeVar

from typing_extensions import Self

from pydantic import Field

from .core_item import HiveCoreItem

if TYPE_CHECKING:
    from ...client import HiveClient


class ClientInfo(HiveCoreItem):
    """Public metadata (name, scopes) for an SSO client id."""

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]
    name: str
    scopes: dict[str, Any]

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)


T = TypeVar("T", bound="ClientInfo")
