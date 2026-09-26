#!/usr/bin/env python3
"""Generate supported API versions file"""

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import (
    BuildHookInterface,
)  # pylint disable=import-error


class GenerateVersionsBuildHook(BuildHookInterface):
    """Hatchling build-hook which generates the supported Hive versions' file dynamically"""

    def initialize(self, version, build_data):
        """Occurs immediately before each build."""

        pyproject = tomllib.loads(
            Path("pyproject.toml").read_text(
                encoding="UTF-8",
            )
        )
        versions = pyproject["tool"]["api_versions"]["supported"]

        dst = Path("pyhive/src/_generated_versions.py")
        dst.write_text(
            "SUPPORTED_API_VERSIONS = " + repr(versions) + "\n"
            "MIN_API_VERSION = SUPPORTED_API_VERSIONS[0]\n"
            "LATEST_API_VERSION = SUPPORTED_API_VERSIONS[-1]\n",
            encoding="UTF-8",
        )

        print(f"+ Generated {dst}")
