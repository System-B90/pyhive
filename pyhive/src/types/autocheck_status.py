"""
Name: autocheck_status.py
Purpose: AutoCheckStatus type definition.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Annotated, Any, TypeVar

from pydantic import Field
from typing_extensions import Self

from ._generated.models import Status as _AutoCheckStatusBase

if TYPE_CHECKING:
    from ...client import HiveClient


class AutoCheckStatus(_AutoCheckStatusBase):
    """An autocheck status entry. Data fields inherited from the generated ``Status`` base."""

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)


T = TypeVar("T", bound="AutoCheckStatus")
