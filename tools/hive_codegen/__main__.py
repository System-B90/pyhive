"""Command-line entry point for hive_codegen.

Usage::

    python -m hive_codegen sync --spec path/to/core.yaml [--repo-root .]
                                [--check] [--no-apply] [--drift-out FILE]
                                [--github-output FILE]

``sync`` regenerates the ``_generated`` layer from the spec, classifies drift
against the committed manifest, and (unless ``--no-apply``) updates the
supported-version list, README and package version. It exits ``0`` when there
are no breaking changes and ``2`` when manual intervention is required.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import load_config
from .drift import classify
from .enums import render_enums_module
from .manifest import build_manifest, load_manifest, write_manifest
from .models import render_models_module
from .project import apply_release_to_project
from .spec import load_spec

EXIT_OK = 0
EXIT_BREAKING = 2


def _format(output_dir: Path) -> None:
    """Best-effort format of generated sources (black ships with the codegen engine)."""

    import subprocess

    for tool in (["black", "-q"], ["ruff", "format"]):
        try:
            subprocess.run(
                [sys.executable, "-m", *tool, str(output_dir / "enums.py"), str(output_dir / "models.py")],
                check=True,
                capture_output=True,
            )
            return
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue


def _write_github_output(path: Path, values: dict[str, str]) -> None:
    with path.open("a", encoding="utf-8") as fh:
        for key, value in values.items():
            fh.write(f"{key}={value}\n")


def _cmd_sync(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    config = load_config(repo_root=repo_root)
    spec = load_spec(Path(args.spec).resolve(), config)
    version = args.version or spec.version

    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "__init__.py").write_text(
        '"""Auto-generated PyHive core layer. Do not edit by hand."""\n', encoding="utf-8"
    )

    old_manifest = load_manifest(output_dir / "manifest.json")
    new_manifest = build_manifest(spec, config)
    report = classify(old_manifest, new_manifest)

    print(report.to_markdown())
    if args.drift_out:
        Path(args.drift_out).write_text(report.to_markdown() + "\n", encoding="utf-8")

    project_changed = False
    if not args.check:
        (output_dir / "enums.py").write_text(render_enums_module(spec), encoding="utf-8")
        (output_dir / "models.py").write_text(render_models_module(spec, config), encoding="utf-8")
        write_manifest(new_manifest, output_dir)
        _format(output_dir)

        if not args.no_apply:
            if report.has_breaking:
                bump = "major"
            elif report.is_empty:
                bump = "patch"
            else:
                bump = "minor"
            summary = apply_release_to_project(repo_root, version, bump)
            project_changed = summary.get("supported_added") == "True"
            print("\nProject files:", summary)

    if args.github_output:
        _write_github_output(
            Path(args.github_output),
            {
                "api_version": version,
                "has_breaking": "true" if report.has_breaking else "false",
                "has_changes": "true" if (not report.is_empty or project_changed) else "false",
            },
        )

    return EXIT_BREAKING if report.has_breaking else EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hive_codegen")
    sub = parser.add_subparsers(dest="command", required=True)

    sync = sub.add_parser("sync", help="regenerate the core layer from a spec")
    sync.add_argument("--spec", required=True, help="path to Hive's api/core.yaml")
    sync.add_argument("--repo-root", default=".", help="PyHive repo root")
    sync.add_argument("--version", default=None, help="override API version (default: spec info.version)")
    sync.add_argument("--check", action="store_true", help="report drift without writing files")
    sync.add_argument("--no-apply", action="store_true", help="skip pyproject/README/version edits")
    sync.add_argument("--drift-out", default=None, help="write the drift report markdown here")
    sync.add_argument("--github-output", default=None, help="append key=value outputs here")
    sync.set_defaults(func=_cmd_sync)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
