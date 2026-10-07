"""Generate the bindings of every API generation from every Hive release's spec.

``hive_versions.toml`` maps each supported Hive release to its generation. For
each generation this merges its releases' specs (see :mod:`merge`) and writes
one package::

    pyhive/src/types/_generated/
    ├── __init__.py
    ├── gen1/  {__init__.py, enums.py, models.py, manifest.json}
    ├── gen2/  …
    ├── enums.py    ← re-exports the newest generation (the curated layer's base)
    └── models.py   ← likewise

Specs are read from ``<specs_dir>/<version>/core.yaml``: the output of
``python -m hive_codegen extract``, cached outside this public repo.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Config
from .drift import DriftReport, classify
from .enums import render_enums_module
from .manifest import MANIFEST_NAME, build_manifest, write_manifest
from .merge import merge_specs
from .models import render_models_module
from .project import parse_version_table
from .spec import Spec, load_spec

_HEADER = '"""Auto-generated PyHive core layer. Do not edit by hand."""\n'


@dataclass
class GenerationResult:
    """What :func:`build_all` produced for one generation."""

    generation: str
    versions: list[str]
    # Shape-breaking drift between consecutive releases the table puts in this
    # generation: each one means the table is wrong, not the merge.
    breaking: list[DriftReport]


def spec_path(specs_dir: Path, version: str) -> Path:
    return specs_dir / version / "core.yaml"


def generations(table: dict[str, str]) -> dict[str, list[str]]:
    """Generation -> its releases, in the table's (release) order."""

    grouped: dict[str, list[str]] = {}
    for version, generation in table.items():
        grouped.setdefault(generation, []).append(version)
    return grouped


def latest_generation(table: dict[str, str]) -> str | None:
    return table[next(reversed(table))] if table else None


def generation_manifest(spec: Spec, config: Config) -> dict[str, Any]:
    """A generation's drift manifest: the merged shape plus the releases it serves."""

    return {**build_manifest(spec, config), "versions": list(spec.versions)}


def _write(path: Path, text: str) -> None:
    # LF on every OS: the files are committed, and CI regenerates them on Linux.
    path.write_text(text, encoding="utf-8", newline="\n")


def _shim(module: str, generation: str) -> str:
    return (
        f'"""Re-export of the newest generation\'s {module}. Do not edit by hand."""\n\n'
        f"from .{generation}.{module} import *  # noqa: F403\n"
    )


def _format(paths: list[Path]) -> None:
    """Best-effort format of generated sources (black ships with the codegen engine)."""

    import subprocess
    import sys

    for tool in (["black", "-q"], ["ruff", "format"]):
        try:
            subprocess.run(
                [sys.executable, "-m", *tool, *map(str, paths)],
                check=True,
                capture_output=True,
            )
            return
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue


def render_generation(spec: Spec, config: Config, package: Path) -> None:
    """Write one generation's package from its merged spec."""

    package.mkdir(parents=True, exist_ok=True)
    _write(package / "__init__.py", _HEADER)
    _write(package / "enums.py", render_enums_module(spec))
    _write(package / "models.py", render_models_module(spec, config))
    write_manifest(generation_manifest(spec, config), package)
    _format([package / "enums.py", package / "models.py"])


def build_all(config: Config, specs_dir: Path) -> list[GenerationResult]:
    """Regenerate every generation listed in ``hive_versions.toml``."""

    table = parse_version_table(
        (config.repo_root / "hive_versions.toml").read_text(encoding="utf-8")
    )
    missing = [v for v in table if not spec_path(specs_dir, v).is_file()]
    if missing:
        raise FileNotFoundError(
            f"no spec for {', '.join(missing)} in {specs_dir}; "
            "run `python -m hive_codegen extract` first"
        )

    output = config.output_dir
    grouped = generations(table)
    results: list[GenerationResult] = []
    for generation, versions in grouped.items():
        specs = [
            load_spec(spec_path(specs_dir, v), config, version=v) for v in versions
        ]
        manifests = [build_manifest(s, config) for s in specs]
        breaking = [
            report
            for report in map(classify, manifests, manifests[1:])
            if report.needs_new_generation
        ]
        render_generation(merge_specs(specs), config, output / generation)
        results.append(GenerationResult(generation, versions, breaking))

    # Drop generations (and the pre-split flat layout) no longer in the table.
    for stale in output.iterdir():
        if stale.is_dir() and stale.name not in grouped and stale.name != "__pycache__":
            shutil.rmtree(stale)
    (output / MANIFEST_NAME).unlink(missing_ok=True)

    newest = latest_generation(table)
    _write(output / "__init__.py", _HEADER)
    for module in ("enums", "models"):
        _write(output / f"{module}.py", _shim(module, str(newest)))
    return results
