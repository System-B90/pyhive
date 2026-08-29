"""
Name: help_notification.py
Purpose: Model for help "latest activity" notifications in Hive.
Created: 2026-08-23
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Annotated, Any, Self, TypeVar

from pydantic import Field

from ._generated.models import HelpNotification as _HelpNotificationBase

if TYPE_CHECKING:
    from ...client import HiveClient


class HelpNotification(_HelpNotificationBase):
    """Latest staff-update marker for a help thread. Data fields are inherited."""

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)


T = TypeVar("T", bound="HelpNotification")
