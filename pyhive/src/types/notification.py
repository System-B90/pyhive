"""
Name: notification.py
Purpose: Model for user notifications in the Hive system.
Created: 2026-08-23
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Annotated, Any, TypeVar

from typing_extensions import Self

from pydantic import Field

from ._generated.models import Notification as _NotificationBase

if TYPE_CHECKING:
    from ...client import HiveClient


class Notification(_NotificationBase):
    """A user notification (help/assignment related). Data fields are inherited."""

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)


T = TypeVar("T", bound="Notification")
