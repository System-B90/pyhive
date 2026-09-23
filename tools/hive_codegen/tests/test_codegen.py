"""Offline unit tests for hive_codegen (no live server required).

Run with: ``pytest tools/hive_codegen/tests``
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from hive_codegen import project
from hive_codegen.drift import classify
from hive_codegen.enums import member_name


@pytest.mark.parametrize(
    ("value", "label", "is_int", "expected"),
    [
        ("On Done", None, False, "ON_DONE"),
        ("Staff Only", None, False, "STAFF_ONLY"),
        ("AutoChecked", None, False, "AUTOCHECKED"),
        ("multiResponse", None, False, "MULTIRESPONSE"),
        ("Work In Progress", None, False, "WORK_IN_PROGRESS"),
        (1, "Hanich", True, "HANICH"),
        (5, "Admin", True, "ADMIN"),
    ],
)
def test_member_name(
    value: object, label: str | None, is_int: bool, expected: str
) -> None:
    assert member_name(value, label, is_int) == expected


def _manifest(version: str, enums=None, models=None, endpoints=None) -> dict:
    return {
        "version": version,
        "enums": enums or {},
        "models": models or {},
        "endpoints": endpoints or {},
    }


def test_drift_first_generation_has_no_breaking() -> None:
    report = classify(None, _manifest("7.1.0"))
    assert not report.has_breaking
    assert report.notes


def test_drift_additive_changes() -> None:
    old = _manifest(
        "7.0.0",
        enums={"E": {"is_int": False, "members": {"A": "A"}}},
        models={"M": {"fields": {"id": {"type": "int", "required": True}}}},
    )
    new = _manifest(
        "7.1.0",
        enums={"E": {"is_int": False, "members": {"A": "A", "B": "B"}}},
        models={
            "M": {
                "fields": {
                    "id": {"type": "int", "required": True},
                    "note": {"type": "str", "required": False},
                }
            },
            "N": {"fields": {}},
        },
        endpoints={
            "/api/core/x/": {"get": {"operationId": "x", "query_params": {"q": "str"}}}
        },
    )
    report = classify(old, new)
    assert not report.has_breaking
    assert any("new member `B`" in a for a in report.additive)
    assert any("new field `note`" in a for a in report.additive)
    assert any("New model `N`" in a for a in report.additive)
    assert any("New endpoint" in a for a in report.additive)


def test_drift_breaking_changes() -> None:
    old = _manifest(
        "7.0.0",
        enums={"E": {"is_int": False, "members": {"A": "A", "B": "B"}}},
        models={
            "M": {
                "fields": {
                    "id": {"type": "int", "required": True},
                    "x": {"type": "int", "required": True},
                }
            }
        },
    )
    new = _manifest(
        "7.1.0",
        enums={"E": {"is_int": False, "members": {"A": "A"}}},
        models={"M": {"fields": {"id": {"type": "str", "required": True}}}},
    )
    report = classify(old, new)
    assert report.has_breaking
    assert any("removed member `B`" in b for b in report.breaking)
    assert any("removed field `x`" in b for b in report.breaking)
    assert any("type" in b and "`id`" in b for b in report.breaking)


PYPROJECT = """\
[project]
name = "PyHiveLMS"
version = "1.4.0"

[tool.api_versions]
supported = ["5.1.2", "6.4.0"]
"""


def test_add_supported_version_sorted() -> None:
    text, changed = project.add_supported_version(PYPROJECT, "6.2.0")
    assert changed
    assert project.parse_supported(text) == ["5.1.2", "6.2.0", "6.4.0"]


def test_add_supported_version_idempotent() -> None:
    text, changed = project.add_supported_version(PYPROJECT, "6.4.0")
    assert not changed
    assert text == PYPROJECT


def test_bump_package_version() -> None:
    text, new = project.bump_package_version(PYPROJECT, "minor")
    assert new == "1.5.0"
    assert 'version = "1.5.0"' in text
    text, new = project.bump_package_version(PYPROJECT, "major")
    assert new == "2.0.0"


def test_update_readme_versions() -> None:
    readme = (
        "Versions:\n<!-- SUPPORTED_API_VERSIONS_START -->\n- `old`\n"
        "<!-- SUPPORTED_API_VERSIONS_END -->\nrest\n"
    )
    out = project.update_readme_versions(readme, ["6.4.0", "5.1.2"])
    assert "- `5.1.2`\n- `6.4.0`" in out
    assert "`old`" not in out
