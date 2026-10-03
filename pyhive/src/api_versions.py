"""
Name: api_versions.py
Purpose: Hive versions PyHive supports and the exact-match lookup from a Hive
    version to the API generation that serves it (#42).
Created: 2026-10-03
Author: Michael K. Steinberg

The table lives in ``hive_versions.toml`` and is rendered into
``_generated_versions.py`` at build time. Hive versions are not semver, so the
lookup is an exact string match: no ranges, no "same major" fallback.
"""

from __future__ import annotations

from pyhive.src._generated_versions import (
    HIVE_VERSION_GENERATIONS,
    LATEST_API_VERSION,
    MIN_API_VERSION,
    SUPPORTED_API_VERSIONS,
)

__all__ = [
    "HIVE_VERSION_GENERATIONS",
    "LATEST_API_VERSION",
    "LATEST_GENERATION",
    "MIN_API_VERSION",
    "SUPPORTED_API_VERSIONS",
    "UnverifiedHiveVersionError",
    "generation_for",
    "versions_for_generation",
]

LATEST_GENERATION: str = HIVE_VERSION_GENERATIONS[LATEST_API_VERSION]


class UnverifiedHiveVersionError(RuntimeError):
    """The Hive version is not in PyHive's table of verified releases."""

    def __init__(self, version: str) -> None:
        self.version = version
        super().__init__(
            f"Unsupported Hive API version '{version}': it is not a Hive release this "
            f"PyHive has verified. Verified versions: {', '.join(SUPPORTED_API_VERSIONS)}. "
            "Upgrade PyHive if the server is newer, or pass skip_version_check=True "
            "to try anyway."
        )


def generation_for(version: str) -> str:
    """Return the API generation serving the exact Hive ``version``.

    Raises:
        UnverifiedHiveVersionError: ``version`` is not in the table.
    """

    try:
        return HIVE_VERSION_GENERATIONS[version]
    except KeyError:
        raise UnverifiedHiveVersionError(version) from None


def versions_for_generation(generation: str) -> list[str]:
    """Every Hive version the table maps to ``generation``, oldest first."""

    return [v for v, g in HIVE_VERSION_GENERATIONS.items() if g == generation]
