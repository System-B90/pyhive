"""Re-export of :class:`ClearanceEnum` from the auto-generated enum layer.

The enum definition lives in ``pyhive/src/types/_generated/enums.py`` and is
regenerated from Hive's OpenAPI spec on each release. This thin module keeps
the historical import path stable.
"""

from .._generated.enums import ClearanceEnum

__all__ = ["ClearanceEnum"]
