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
"""

VERSIONS_TABLE = """\
# header comment survives
[versions]
"5.1.2" = "gen1"
"6.4.0" = "gen2"
"""


def test_add_supported_version_sorted_maps_to_latest_generation() -> None:
    text, changed = project.add_supported_version(VERSIONS_TABLE, "7.0.0")
    assert changed
    assert project.parse_supported(text) == ["5.1.2", "6.4.0", "7.0.0"]
    assert project.parse_version_table(text)["7.0.0"] == "gen2"
    assert text.startswith("# header comment survives\n")


def test_add_supported_version_appends_whatever_the_number() -> None:
    # Release order, not version order: Hive's numbers are not ordered.
    text, changed = project.add_supported_version(VERSIONS_TABLE, "6.2.0", "gen1")
    assert changed
    assert list(project.parse_version_table(text)) == ["5.1.2", "6.4.0", "6.2.0"]
    assert project.parse_version_table(text)["6.2.0"] == "gen1"


def test_add_supported_version_explicit_new_generation() -> None:
    text, _ = project.add_supported_version(VERSIONS_TABLE, "8.0.0", "gen3")
    assert project.parse_version_table(text)["8.0.0"] == "gen3"


def test_add_supported_version_idempotent() -> None:
    text, changed = project.add_supported_version(VERSIONS_TABLE, "6.4.0")
    assert not changed
    assert text == VERSIONS_TABLE


def test_apply_release_to_project(tmp_path: Path) -> None:
    (tmp_path / "hive_versions.toml").write_text(VERSIONS_TABLE, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    summary = project.apply_release_to_project(tmp_path, "7.0.0", "minor")
    assert summary == {"supported_added": "True", "package_version": "1.5.0"}
    table = project.parse_version_table(
        (tmp_path / "hive_versions.toml").read_text("utf-8")
    )
    assert table["7.0.0"] == "gen2"
    again = project.apply_release_to_project(tmp_path, "7.0.0", "minor")
    assert again == {"supported_added": "False"}
    assert 'version = "1.5.0"' in (tmp_path / "pyproject.toml").read_text("utf-8")


def test_next_generation() -> None:
    assert project.next_generation({"5.1.2": "gen1", "7.3.0": "gen2"}) == "gen3"
    assert project.next_generation({}) == "gen1"
    assert project.next_generation({"x": "custom", "y": "gen4"}) == "gen5"


def test_breaking_release_gets_a_new_generation(tmp_path: Path) -> None:
    (tmp_path / "hive_versions.toml").write_text(VERSIONS_TABLE, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    summary = project.apply_release_to_project(
        tmp_path, "6.5.0", "major", breaking=True
    )
    assert summary["generation"] == "gen3"
    assert summary["new_generation"] == "True"
    table = project.parse_version_table(
        (tmp_path / "hive_versions.toml").read_text("utf-8")
    )
    # Never auto-mapped to the previous generation, whatever the number says.
    assert table["6.5.0"] == "gen3"
    assert table["6.4.0"] == "gen2"


def test_breaking_rerun_keeps_the_existing_mapping(tmp_path: Path) -> None:
    (tmp_path / "hive_versions.toml").write_text(VERSIONS_TABLE, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    again = project.apply_release_to_project(tmp_path, "6.4.0", "major", breaking=True)
    assert again == {"supported_added": "False"}


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
    assert "- `6.4.0`\n- `5.1.2`" in out
    assert "`old`" not in out
