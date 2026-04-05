"""
Name: help_response_segel_nested.py
Purpose: Model definition for nested help responses in the Hive system.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

import datetime
from typing import TYPE_CHECKING, Any, Self, TypeVar

from pydantic import Field

from .core_item import HiveCoreItem
from .enums.help_response_type_enum import HelpResponseTypeEnum

if TYPE_CHECKING:
    from ...client import HiveClient


class HelpResponseSegelNested(HiveCoreItem):
    """Attributes:
    id (int):
    user (int):
    date (datetime.datetime):
    response_type (HelpResponseTypeEnum):
        * `Resolve` - Resolve
        * `Open` - Open
        * `Comment` - Comment
    contents (str | None):
    file_name (str | None):
    dear_student (bool):  Default: True.
    hide_checker_name (bool | None):
    segel_only (bool | None):

    """

    hive_client: "HiveClient" = Field(exclude=True, repr=False)
    id: int
    user: int
    date: datetime.datetime
    response_type: HelpResponseTypeEnum
    contents: str | None = Field(default=None)
    file_name: str | None = Field(default=None)
    dear_student: bool = Field(default=True)
    hide_checker_name: bool | None = Field(default=None)
    segel_only: bool | None = Field(default=None)

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)


T = TypeVar("T", bound="HelpResponseSegelNested")
