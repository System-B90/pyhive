"""
Name: core_item.py
Purpose: Defines the base Pydantic model for Hive core items.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from typing import Any

from pydantic import BaseModel, ConfigDict


class HiveCoreItem(BaseModel):
    """
    Base Pydantic model for Hive core items.
    Standardizes configuration and default serialization behavior.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )

    def to_dict(self) -> dict[str, Any]:
        """
        Serializes the instance to a dictionary, omitting unset fields.

        Returns:
            dict[str, Any]: The payload formatted for API requests.
        """
        return self.model_dump(mode="json", by_alias=True, exclude_unset=True)
