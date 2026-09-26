"""
Name: top_help_response_checker.py
Purpose: Model for aggregated top checker responses on a help request.
Created: 2026-08-23
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Annotated, Any, TypeVar

from pydantic import Field
from typing_extensions import Self

from ._generated.models import (
    TopHelpResponseChecker as _TopHelpResponseCheckerBase,
)

if TYPE_CHECKING:
    from ...client import HiveClient


class TopHelpResponseChecker(_TopHelpResponseCheckerBase):
    """One of the most frequent checker responses for a help request."""

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)


T = TypeVar("T", bound="TopHelpResponseChecker")
