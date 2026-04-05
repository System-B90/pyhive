"""
Name: autocheck_status.py
Purpose: AutoCheckStatus type definition.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

import datetime
from typing import TYPE_CHECKING, Any, Self, TypeVar

from pydantic import Field

from .core_item import HiveCoreItem
from .enums.action_enum import ActionEnum

if TYPE_CHECKING:
    from ...client import HiveClient


class AutoCheckStatus(HiveCoreItem):
    """

    Attributes:
        id (int):
        time (datetime.datetime):
        action (ActionEnum):
            * `Handling` - Handling
            * `No Check` - Nocheck
            * `Built` - Built
            * `Finished` - Finished
            * `Sending` - Sending
            * `Error` - Error
            * `Success` - Success
        payload (str | None):

    """

    hive_client: "HiveClient" = Field(exclude=True, repr=False)
    id: int
    time: datetime.datetime
    action: ActionEnum
    payload: str | None = Field(default=None)

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)


T = TypeVar("T", bound="AutoCheckStatus")
