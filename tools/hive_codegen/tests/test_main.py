"""Offline unit tests for hive_codegen.__main__._cmd_sync (version-bump
decision, exit codes, --check, --github-output)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import hive_codegen.__main__ as main_module
from hive_codegen.config import Config
from hive_codegen.spec import Spec

EMPTY_SPEC = Spec(version="7.2.0", raw={}, object_schemas={}, enums={}, endpoints={})


def _args(tmp_path: Path, **overrides: object) -> argparse.Namespace:
    defaults: dict[str, object] = {
        "repo_root": str(tmp_path),
        "spec": "unused.yaml",
        "version": None,
        "check": False,
        "no_apply": False,
        "drift_out": None,
        "github_output": None,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


@pytest.fixture(autouse=True)
def patched_pipeline(monkeypatch, tmp_path: Path):
    """Stub every step of _cmd_sync except classify/version-bump decision
    itself, which is the highest-risk logic per the issue this covers."""

    output_dir = tmp_path / "generated"
    config = Config(
        output_package=str(output_dir.relative_to(tmp_path)),
        base_class="pyhive.src.types.core_item.HiveCoreItem",
        noise_name_contains=(),
        aliases={},
        force_optional=(),
        force_nullable=(),
        skip_fields=(),
        model_to_schema={},
        curated_only_models=(),
        curated_only_enums=(),
        repo_root=tmp_path,
    )

    monkeypatch.setattr(main_module, "load_config", lambda repo_root: config)
    monkeypatch.setattr(main_module, "load_spec", lambda path, cfg: EMPTY_SPEC)
    monkeypatch.setattr(main_module, "render_enums_module", lambda spec: "# enums")
    monkeypatch.setattr(
        main_module, "render_models_module", lambda spec, cfg: "# models"
    )
    monkeypatch.setattr(main_module, "_format", lambda output_dir: None)

    applied: dict[str, object] = {}

    def _fake_apply(repo_root, version, bump):
        applied["bump"] = bump
        return {"supported_added": "False"}

    monkeypatch.setattr(main_module, "apply_release_to_project", _fake_apply)
    return {"config": config, "applied": applied}


def _set_manifests(monkeypatch, old, new):
    monkeypatch.setattr(main_module, "load_manifest", lambda path: old)
    monkeypatch.setattr(main_module, "build_manifest", lambda spec, cfg: new)


def test_breaking_change_selects_major_bump_and_exit_2(
    monkeypatch, tmp_path, patched_pipeline
):
    old = {
        "version": "7.1.0",
        "enums": {},
        "models": {"M": {"fields": {"x": {"type": "int", "required": True}}}},
        "endpoints": {},
    }
    new = {
        "version": "7.2.0",
        "enums": {},
        "models": {"M": {"fields": {}}},
        "endpoints": {},
    }
    _set_manifests(monkeypatch, old, new)

    rc = main_module._cmd_sync(_args(tmp_path))

    assert rc == main_module.EXIT_BREAKING
    assert patched_pipeline["applied"]["bump"] == "major"


def test_empty_diff_selects_patch_bump_and_exit_0(
    monkeypatch, tmp_path, patched_pipeline
):
    manifest = {"version": "7.2.0", "enums": {}, "models": {}, "endpoints": {}}
    _set_manifests(monkeypatch, manifest, dict(manifest))

    rc = main_module._cmd_sync(_args(tmp_path))

    assert rc == main_module.EXIT_OK
    assert patched_pipeline["applied"]["bump"] == "patch"


def test_additive_only_selects_minor_bump_and_exit_0(
    monkeypatch, tmp_path, patched_pipeline
):
    old = {"version": "7.1.0", "enums": {}, "models": {}, "endpoints": {}}
    new = {
        "version": "7.2.0",
        "enums": {},
        "models": {"N": {"fields": {}}},
        "endpoints": {},
    }
    _set_manifests(monkeypatch, old, new)

    rc = main_module._cmd_sync(_args(tmp_path))

    assert rc == main_module.EXIT_OK
    assert patched_pipeline["applied"]["bump"] == "minor"


def test_check_mode_writes_nothing(monkeypatch, tmp_path, patched_pipeline):
    manifest = {"version": "7.2.0", "enums": {}, "models": {}, "endpoints": {}}
    _set_manifests(monkeypatch, manifest, dict(manifest))

    write_calls: list[object] = []
    monkeypatch.setattr(
        main_module, "write_manifest", lambda *a, **kw: write_calls.append(a)
    )

    rc = main_module._cmd_sync(_args(tmp_path, check=True))

    assert rc == main_module.EXIT_OK
    assert write_calls == []
    assert (
        "applied" not in patched_pipeline or "bump" not in patched_pipeline["applied"]
    )
    output_dir = patched_pipeline["config"].output_dir
    assert not (output_dir / "enums.py").exists()
    assert not (output_dir / "models.py").exists()


def test_no_apply_skips_version_bump(monkeypatch, tmp_path, patched_pipeline):
    manifest = {"version": "7.2.0", "enums": {}, "models": {}, "endpoints": {}}
    _set_manifests(monkeypatch, manifest, dict(manifest))
    monkeypatch.setattr(main_module, "write_manifest", lambda *a, **kw: None)

    rc = main_module._cmd_sync(_args(tmp_path, no_apply=True))

    assert rc == main_module.EXIT_OK
    assert "bump" not in patched_pipeline["applied"]


def test_github_output_written(monkeypatch, tmp_path, patched_pipeline):
    old = {
        "version": "7.1.0",
        "enums": {},
        "models": {"M": {"fields": {"x": {"type": "int", "required": True}}}},
        "endpoints": {},
    }
    new = {
        "version": "7.2.0",
        "enums": {},
        "models": {"M": {"fields": {}}},
        "endpoints": {},
    }
    _set_manifests(monkeypatch, old, new)
    monkeypatch.setattr(main_module, "write_manifest", lambda *a, **kw: None)

    out_path = tmp_path / "gh_output.txt"
    rc = main_module._cmd_sync(_args(tmp_path, github_output=str(out_path)))

    assert rc == main_module.EXIT_BREAKING
    content = out_path.read_text(encoding="utf-8")
    assert "api_version=7.2.0" in content
    assert "has_breaking=true" in content
    assert "has_changes=true" in content
