"""Base class for Hive core items."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self


class HiveCoreItem:
    """Base class for Hive core items."""

    def to_dict(self) -> dict[str, Any]:
        """Serialize this HiveCoreItem instance to a plain dictionary."""
        raise NotImplementedError

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any], *args: Any, **kwargs: Any) -> Self:  # noqa: D102
        """Deserialize a HiveCoreItem instance from a mapping."""
        raise NotImplementedError
