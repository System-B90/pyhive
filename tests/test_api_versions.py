"""
Name: test_api_versions.py
Purpose: Offline tests for the hive_versions.toml table, its generated module
    and the exact-match Hive version -> generation lookup (#42).
Created: 2026-10-03
Author: Michael K. Steinberg
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

from pyhive.client.client import HiveClient
from pyhive.src import _generated_versions
from pyhive.src.api_versions import (
    HIVE_VERSION_GENERATIONS,
    LATEST_API_VERSION,
    LATEST_GENERATION,
    SUPPORTED_API_VERSIONS,
    UnverifiedHiveVersionError,
    generation_for,
    versions_for_generation,
)

# The table tests need a TOML parser; Python 3.10 only has one when tomli is installed.
tomllib = pytest.importorskip("tomllib" if sys.version_info >= (3, 11) else "tomli")

ROOT = Path(__file__).resolve().parent.parent


def _load_generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "generate_versions", ROOT / "scripts" / "generate_versions.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_versions"] = module
    spec.loader.exec_module(module)
    return module


def test_generated_module_is_in_sync_with_the_table() -> None:
    generator = _load_generator()
    expected = generator.render(
        (ROOT / "hive_versions.toml").read_text(encoding="utf-8")
    )
    actual = (ROOT / "pyhive" / "src" / "_generated_versions.py").read_text(
        encoding="utf-8"
    )
    assert actual.replace("\r\n", "\n") == expected, (
        "run `python scripts/generate_versions.py` after editing hive_versions.toml"
    )


def test_table_matches_runtime_constants() -> None:
    table = tomllib.loads((ROOT / "hive_versions.toml").read_text(encoding="utf-8"))
    assert HIVE_VERSION_GENERATIONS == table["versions"]
    assert SUPPORTED_API_VERSIONS == list(_generated_versions.HIVE_VERSION_GENERATIONS)


def test_render_keeps_the_tables_release_order() -> None:
    # Hive version numbers are not ordered: the newest release is the last
    # entry, even when its number is "lower".
    generator = _load_generator()
    namespace: dict[str, object] = {}
    exec(  # noqa: S102 - executing our own generated source
        generator.render('[versions]\n"10.0.0" = "g1"\n"9.1.0" = "g2"\n'), namespace
    )
    assert namespace["SUPPORTED_API_VERSIONS"] == ["10.0.0", "9.1.0"]
    assert namespace["LATEST_API_VERSION"] == "9.1.0"


@pytest.mark.parametrize(
    "version", ["5.11.1", "5.12.0", "6.0.1", "6.1.1", "6.2.0", "6.3.0", "6.4.0"]
)
def test_integer_id_releases_map_to_gen1(version: str) -> None:
    assert generation_for(version) == "gen1"


@pytest.mark.parametrize("version", ["7.0.1", "7.1.0", "7.2.0", "7.3.0"])
def test_uuid_releases_map_to_gen2(version: str) -> None:
    assert generation_for(version) == "gen2"


def test_stale_reporting_releases_are_not_listed() -> None:
    # v5.1.2's server reports 5.0.0, so an entry for it could never match.
    with pytest.raises(UnverifiedHiveVersionError):
        generation_for("5.1.2")


def test_latest_generation_serves_latest_version() -> None:
    assert LATEST_GENERATION == generation_for(LATEST_API_VERSION)
    assert LATEST_API_VERSION in versions_for_generation(LATEST_GENERATION)


@pytest.mark.parametrize("version", ["7.3.1", "7.3", "7", "8.0.0", "", "7.3.0 "])
def test_unlisted_versions_are_unverified_even_when_close(version: str) -> None:
    with pytest.raises(UnverifiedHiveVersionError) as exc:
        generation_for(version)
    assert exc.value.version == version
    assert isinstance(exc.value, RuntimeError)
    assert LATEST_API_VERSION in str(exc.value)


def test_versions_for_generation() -> None:
    assert versions_for_generation("gen2") == ["7.0.1", "7.1.0", "7.2.0", "7.3.0"]
    assert versions_for_generation("nope") == []


class _StubServer:
    def __init__(self, version: str) -> None:
        self.version = version

    def get_hive_version(self) -> str:
        return self.version


def test_client_version_check_accepts_listed_release() -> None:
    HiveClient._api_version_check(_StubServer("7.2.0"))  # type: ignore[arg-type]


def test_client_version_check_rejects_unlisted_patch_release() -> None:
    with pytest.raises(UnverifiedHiveVersionError):
        HiveClient._api_version_check(_StubServer("7.3.1"))  # type: ignore[arg-type]
