"""Offline unit tests for hive_codegen.__main__._cmd_sync (version-bump
decision, exit codes, --check, --github-output, the rebuild it triggers)."""

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
        "spec": str(tmp_path / "core.yaml"),
        "specs_dir": str(tmp_path / "specs"),
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
    monkeypatch.setattr(
        main_module, "load_spec", lambda path, cfg, version=None: EMPTY_SPEC
    )
    (tmp_path / "core.yaml").write_text("openapi: 3.0.3\n", encoding="utf-8")
    (tmp_path / "hive_versions.toml").write_text(
        '[versions]\n"7.1.0" = "gen3"\n', encoding="utf-8"
    )
    builds: list[Path] = []

    def _fake_build(repo_root: Path, specs_dir: Path) -> bool:
        builds.append(specs_dir)
        return False

    monkeypatch.setattr(main_module, "_build", _fake_build)

    applied: dict[str, object] = {}

    def _fake_apply(repo_root, version, bump, *, breaking=False):
        applied["bump"] = bump
        applied["breaking"] = breaking
        generation = {"generation": "gen9"} if breaking else {}
        return {"supported_added": "False", **generation}

    monkeypatch.setattr(main_module, "apply_release_to_project", _fake_apply)
    return {"config": config, "applied": applied, "builds": builds}


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
    assert patched_pipeline["applied"]["breaking"] is True


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

    rc = main_module._cmd_sync(_args(tmp_path, check=True, specs_dir=None))

    assert rc == main_module.EXIT_OK
    assert patched_pipeline["builds"] == []
    assert (
        "applied" not in patched_pipeline or "bump" not in patched_pipeline["applied"]
    )
    output_dir = patched_pipeline["config"].output_dir
    assert not (output_dir / "enums.py").exists()
    assert not (output_dir / "models.py").exists()


def test_no_apply_skips_version_bump(monkeypatch, tmp_path, patched_pipeline):
    manifest = {"version": "7.2.0", "enums": {}, "models": {}, "endpoints": {}}
    _set_manifests(monkeypatch, manifest, dict(manifest))

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

    out_path = tmp_path / "gh_output.txt"
    rc = main_module._cmd_sync(_args(tmp_path, github_output=str(out_path)))

    assert rc == main_module.EXIT_BREAKING
    content = out_path.read_text(encoding="utf-8")
    assert "api_version=7.2.0" in content
    assert "has_breaking=true" in content
    assert "has_changes=true" in content
    assert "new_generation=gen9" in content


def test_sync_caches_the_spec_and_rebuilds(monkeypatch, tmp_path, patched_pipeline):
    manifest = {"version": "7.2.0", "enums": {}, "models": {}, "endpoints": {}}
    _set_manifests(monkeypatch, manifest, dict(manifest))

    rc = main_module._cmd_sync(_args(tmp_path))

    assert rc == main_module.EXIT_OK
    assert patched_pipeline["builds"] == [(tmp_path / "specs").resolve()]
    cached = tmp_path / "specs" / "7.2.0" / "core.yaml"
    assert cached.read_text(encoding="utf-8") == "openapi: 3.0.3\n"


def test_sync_without_specs_dir_refuses_to_write(
    monkeypatch, tmp_path, patched_pipeline
):
    rc = main_module._cmd_sync(_args(tmp_path, specs_dir=None))

    assert rc == main_module.EXIT_BREAKING
    assert "bump" not in patched_pipeline["applied"]


def test_baseline_is_the_newest_generations_manifest(
    monkeypatch, tmp_path, patched_pipeline
):
    seen: list[Path] = []
    monkeypatch.setattr(
        main_module, "load_manifest", lambda path: seen.append(path) or None
    )
    monkeypatch.setattr(
        main_module,
        "build_manifest",
        lambda spec, cfg: {"version": "7.2.0", "enums": {}, "models": {}},
    )

    main_module._cmd_sync(_args(tmp_path, check=True))

    output_dir = patched_pipeline["config"].output_dir
    assert seen == [output_dir / "gen3" / "manifest.json"]
