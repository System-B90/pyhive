"""
Name: powersync_token.py
Purpose: Model for PowerSync streaming credentials issued by Hive.
Created: 2026-08-23
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Annotated, Any, TypeVar

from typing_extensions import Self

from pydantic import Field

from ._generated.models import PowerSyncToken as _PowerSyncTokenBase

if TYPE_CHECKING:
    from ...client import HiveClient


class PowerSyncToken(_PowerSyncTokenBase):
    """PowerSync endpoint + short-lived JWT. Data fields are inherited."""

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)


T = TypeVar("T", bound="PowerSyncToken")
