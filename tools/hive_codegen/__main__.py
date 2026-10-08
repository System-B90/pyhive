"""Command-line entry point for hive_codegen.

Usage::

    python -m hive_codegen extract --hive-repo ../Hive --specs-dir SPECS
                                   [--version 7.3.0 ...] [--force]
    python -m hive_codegen build --specs-dir SPECS [--repo-root .]
    python -m hive_codegen sync --spec path/to/core.yaml --specs-dir SPECS
                                [--repo-root .] [--check] [--no-apply]
                                [--drift-out FILE] [--github-output FILE]

``extract`` runs ``generate_api`` for each Hive release in ``hive_versions.toml``
whose spec is not cached in ``SPECS`` yet. ``build`` regenerates one bindings
package per API generation from those specs. ``sync`` classifies a new
release's drift against the newest generation, maps it in ``hive_versions.toml``
(unless ``--no-apply``) and rebuilds. ``build`` and ``sync`` exit ``0`` when
there are no breaking changes and ``2`` when manual intervention is required.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from .build import build_all, latest_generation, spec_path
from .config import load_config
from .drift import classify
from .extract import extract_spec
from .manifest import MANIFEST_NAME, build_manifest, load_manifest
from .project import apply_release_to_project, parse_version_table
from .spec import load_spec

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_BREAKING = 2


def _write_github_output(path: Path, values: dict[str, str]) -> None:
    with path.open("a", encoding="utf-8") as fh:
        for key, value in values.items():
            fh.write(f"{key}={value}\n")


def _read_table(repo_root: Path) -> dict[str, str]:
    return parse_version_table(
        (repo_root / "hive_versions.toml").read_text(encoding="utf-8")
    )


def _build(repo_root: Path, specs_dir: Path) -> bool:
    """Rebuild every generation. Returns whether the table mixes incompatible releases."""

    results = build_all(load_config(repo_root=repo_root), specs_dir)
    mixed = False
    for result in results:
        print(f"{result.generation}: {', '.join(result.versions)}")
        for report in result.breaking:
            mixed = True
            print(
                f"::warning::hive_versions.toml puts {report.from_version} and "
                f"{report.to_version} in {result.generation}, but the drift "
                "between them changes the models' shape:"
            )
            print(report.to_markdown())
    return mixed


def _cmd_extract(args: argparse.Namespace) -> int:
    hive_repo = Path(args.hive_repo).resolve()
    specs_dir = Path(args.specs_dir).resolve()
    versions = args.version or list(_read_table(Path(args.repo_root).resolve()))
    failed: list[str] = []
    for version in versions:
        out = spec_path(specs_dir, version)
        if out.is_file() and not args.force:
            print(f"{version}: cached")
            continue
        print(f"{version}: generating from v{version}", flush=True)
        try:
            extract_spec(hive_repo, f"v{version}", out)
        except (subprocess.CalledProcessError, RuntimeError) as exc:
            print(f"::error::{version}: {exc}", flush=True)
            failed.append(version)
    if failed:
        print(f"Spec generation failed for {', '.join(failed)}")
        return EXIT_FAILED
    return EXIT_OK


def _cmd_build(args: argparse.Namespace) -> int:
    mixed = _build(Path(args.repo_root).resolve(), Path(args.specs_dir).resolve())
    return EXIT_BREAKING if mixed else EXIT_OK


def _cmd_sync(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    config = load_config(repo_root=repo_root)
    spec = load_spec(Path(args.spec).resolve(), config, version=args.version)
    version = spec.version
    if not args.check and not args.specs_dir:
        print("sync needs --specs-dir to rebuild the bindings (or pass --check)")
        return EXIT_BREAKING

    newest = latest_generation(_read_table(repo_root))
    old_manifest = (
        load_manifest(config.output_dir / newest / MANIFEST_NAME) if newest else None
    )
    new_manifest = build_manifest(spec, config)
    report = classify(old_manifest, new_manifest)

    print(report.to_markdown())
    if args.drift_out:
        Path(args.drift_out).write_text(report.to_markdown() + "\n", encoding="utf-8")

    project_changed = False
    new_generation = ""
    mixed = False
    if not args.check:
        if not args.no_apply:
            if report.has_breaking:
                bump = "major"
            elif report.is_empty:
                bump = "patch"
            else:
                bump = "minor"
            summary = apply_release_to_project(
                repo_root, version, bump, breaking=report.needs_new_generation
            )
            project_changed = summary.get("supported_added") == "True"
            new_generation = summary.get("generation", "")
            print("\nProject files:", summary)

        specs_dir = Path(args.specs_dir).resolve()
        cached = spec_path(specs_dir, version)
        if cached.resolve() != Path(args.spec).resolve():
            cached.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(args.spec, cached)
        mixed = _build(repo_root, specs_dir)

    if args.github_output:
        _write_github_output(
            Path(args.github_output),
            {
                "api_version": version,
                "new_generation": new_generation,
                "has_breaking": "true" if report.has_breaking or mixed else "false",
                "has_changes": "true"
                if (not report.is_empty or project_changed)
                else "false",
            },
        )

    return EXIT_BREAKING if report.has_breaking or mixed else EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hive_codegen")
    sub = parser.add_subparsers(dest="command", required=True)

    extract = sub.add_parser(
        "extract", help="run generate_api for each Hive release in the table"
    )
    extract.add_argument("--hive-repo", required=True, help="local Hive checkout")
    extract.add_argument("--specs-dir", required=True, help="spec cache directory")
    extract.add_argument("--repo-root", default=".", help="PyHive repo root")
    extract.add_argument(
        "--version",
        action="append",
        help="Hive version to extract (repeatable; default: every listed one)",
    )
    extract.add_argument(
        "--force", action="store_true", help="regenerate specs that are cached"
    )
    extract.set_defaults(func=_cmd_extract)

    build = sub.add_parser("build", help="regenerate every generation's bindings")
    build.add_argument("--specs-dir", required=True, help="spec cache directory")
    build.add_argument("--repo-root", default=".", help="PyHive repo root")
    build.set_defaults(func=_cmd_build)

    sync = sub.add_parser("sync", help="add a Hive release and rebuild the bindings")
    sync.add_argument("--spec", required=True, help="the release's generated core.yaml")
    sync.add_argument("--specs-dir", default=None, help="spec cache directory")
    sync.add_argument("--repo-root", default=".", help="PyHive repo root")
    sync.add_argument(
        "--version",
        default=None,
        help="override API version (default: spec info.version)",
    )
    sync.add_argument(
        "--check", action="store_true", help="report drift without writing files"
    )
    sync.add_argument(
        "--no-apply", action="store_true", help="skip pyproject/README/version edits"
    )
    sync.add_argument(
        "--drift-out", default=None, help="write the drift report markdown here"
    )
    sync.add_argument(
        "--github-output", default=None, help="append key=value outputs here"
    )
    sync.set_defaults(func=_cmd_sync)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
