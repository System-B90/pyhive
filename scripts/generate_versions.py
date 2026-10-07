#!/usr/bin/env python3
"""
Name: generate_versions.py
Purpose: Render pyhive/src/_generated_versions.py from hive_versions.toml, as a
    hatch build hook or standalone (`python scripts/generate_versions.py`).
Created: 2026-10-03
Author: Michael K. Steinberg
"""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # Python 3.10
    import tomli as tomllib

ROOT = Path(__file__).resolve().parent.parent
TABLE = ROOT / "hive_versions.toml"
DESTINATION = ROOT / "pyhive" / "src" / "_generated_versions.py"


def render(table_text: str) -> str:
    """Render the generated module for the ``[versions]`` table in ``table_text``."""

    # Release order is the table's order: Hive version numbers are not ordered.
    ordered: dict[str, str] = tomllib.loads(table_text)["versions"]
    return (
        "# Generated from hive_versions.toml by scripts/generate_versions.py. Do not edit.\n"
        f"HIVE_VERSION_GENERATIONS = {ordered!r}\n"
        "SUPPORTED_API_VERSIONS = list(HIVE_VERSION_GENERATIONS)\n"
        "MIN_API_VERSION = SUPPORTED_API_VERSIONS[0]\n"
        "LATEST_API_VERSION = SUPPORTED_API_VERSIONS[-1]\n"
    )


def write() -> Path:
    """Regenerate the module on disk and return its path."""

    DESTINATION.write_text(render(TABLE.read_text(encoding="utf-8")), encoding="utf-8")
    return DESTINATION


try:
    from hatchling.builders.hooks.plugin.interface import BuildHookInterface
except ImportError:  # standalone use without hatchling installed
    pass
else:

    class GenerateVersionsBuildHook(BuildHookInterface):  # type: ignore[type-arg]
        """Hatchling build hook that regenerates the supported-versions module."""

        def initialize(self, version: str, build_data: dict[str, object]) -> None:
            """Occurs immediately before each build."""

            print(f"+ Generated {write()}")


if __name__ == "__main__":
    print(f"+ Generated {write()}")
