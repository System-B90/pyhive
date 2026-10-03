"""Update PyHive project files (hive_versions.toml, pyproject.toml, README.md) for a new release."""

from __future__ import annotations

import re
from pathlib import Path

import tomllib

_VERSIONS_SECTION_RE = re.compile(r"(?ms)^\[versions\]\s*\n(?P<body>.*?)(?=^\[|\Z)")
_PKG_VERSION_RE = re.compile(
    r'(?m)^(?P<head>version\s*=\s*")(?P<ver>\d+\.\d+\.\d+)(?P<tail>")'
)
_README_BLOCK_RE = re.compile(
    r"(?P<start><!-- SUPPORTED_API_VERSIONS_START -->\n).*?(?P<end><!-- SUPPORTED_API_VERSIONS_END -->)",
    re.DOTALL,
)


def semver_key(v: str) -> tuple[int, ...]:
    return tuple(int(p) for p in v.split(".")[:3])


def parse_version_table(table_text: str) -> dict[str, str]:
    """The ``[versions]`` table of ``hive_versions.toml``: exact Hive version -> generation."""

    return dict(tomllib.loads(table_text).get("versions", {}))


def parse_supported(table_text: str) -> list[str]:
    return sorted(parse_version_table(table_text), key=semver_key)


def add_supported_version(
    table_text: str, version: str, generation: str | None = None
) -> tuple[str, bool]:
    """Map ``version`` in ``hive_versions.toml``. Returns (text, changed).

    ``generation`` defaults to the one serving the newest listed version,
    i.e. an additive release. A breaking release needs a new generation,
    which the caller must pass explicitly; it is never inferred from the
    version number.
    """

    table = parse_version_table(table_text)
    if version in table:
        return table_text, False
    if generation is None:
        if not table:
            raise ValueError("hive_versions.toml has no [versions] entries to extend")
        generation = table[max(table, key=semver_key)]
    table[version] = generation
    body = "".join(f'"{v}" = "{table[v]}"\n' for v in sorted(table, key=semver_key))
    match = _VERSIONS_SECTION_RE.search(table_text)
    if not match:
        raise ValueError("hive_versions.toml has no [versions] section")
    updated = table_text[: match.start("body")] + body + table_text[match.end("body") :]
    return updated, True


def bump_package_version(pyproject_text: str, part: str) -> tuple[str, str]:
    """Bump the ``[project].version`` (first match). Returns (text, new_version)."""

    m = _PKG_VERSION_RE.search(pyproject_text)
    if not m:
        raise ValueError("project version not found")
    major, minor, patch = (int(x) for x in m.group("ver").split("."))
    if part == "major":
        major, minor, patch = major + 1, 0, 0
    elif part == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    new_version = f"{major}.{minor}.{patch}"
    updated = _PKG_VERSION_RE.sub(
        lambda mm: f"{mm.group('head')}{new_version}{mm.group('tail')}",
        pyproject_text,
        count=1,
    )
    return updated, new_version


def update_readme_versions(readme_text: str, versions: list[str]) -> str:
    bullets = "\n".join(f"- `{v}`" for v in sorted(versions, key=semver_key))
    return _README_BLOCK_RE.sub(
        lambda m: f"{m.group('start')}{bullets}\n{m.group('end')}", readme_text, count=1
    )


def apply_release_to_project(
    repo_root: Path, api_version: str, package_bump: str
) -> dict[str, str]:
    """Apply all project-file edits for a synced Hive release. Returns a summary."""

    summary: dict[str, str] = {}
    table_path = repo_root / "hive_versions.toml"
    table_text, added = add_supported_version(
        table_path.read_text(encoding="utf-8"), api_version
    )
    summary["supported_added"] = str(added)
    if added:
        table_path.write_text(table_text, encoding="utf-8")
        pyproject = repo_root / "pyproject.toml"
        text, new_pkg = bump_package_version(
            pyproject.read_text(encoding="utf-8"), package_bump
        )
        pyproject.write_text(text, encoding="utf-8")
        summary["package_version"] = new_pkg

    readme = repo_root / "README.md"
    if readme.exists():
        rtext = readme.read_text(encoding="utf-8")
        readme.write_text(
            update_readme_versions(rtext, parse_supported(table_text)), encoding="utf-8"
        )
    return summary
