"""Update PyHive project files (pyproject.toml, README.md) for a new release."""

from __future__ import annotations

import re
from pathlib import Path

_SUPPORTED_RE = re.compile(
    r"(?P<head>\[tool\.api_versions\]\s*\nsupported\s*=\s*)\[(?P<body>[^\]]*)\]"
)
_PKG_VERSION_RE = re.compile(
    r'(?m)^(?P<head>version\s*=\s*")(?P<ver>\d+\.\d+\.\d+)(?P<tail>")'
)
_README_BLOCK_RE = re.compile(
    r"(?P<start><!-- SUPPORTED_API_VERSIONS_START -->\n).*?(?P<end><!-- SUPPORTED_API_VERSIONS_END -->)",
    re.DOTALL,
)


def semver_key(v: str) -> tuple[int, ...]:
    return tuple(int(p) for p in v.split(".")[:3])


def parse_supported(pyproject_text: str) -> list[str]:
    m = _SUPPORTED_RE.search(pyproject_text)
    if not m:
        return []
    return re.findall(r'"([^"]+)"', m.group("body"))


def add_supported_version(pyproject_text: str, version: str) -> tuple[str, bool]:
    """Add ``version`` to ``[tool.api_versions].supported`` (sorted). Returns (text, changed)."""

    current = parse_supported(pyproject_text)
    if version in current:
        return pyproject_text, False
    new = sorted({*current, version}, key=semver_key)
    rendered = "[" + ", ".join(f'"{v}"' for v in new) + "]"
    updated = _SUPPORTED_RE.sub(
        lambda m: m.group("head") + rendered, pyproject_text, count=1
    )
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
    pyproject = repo_root / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    text, added = add_supported_version(text, api_version)
    summary["supported_added"] = str(added)
    if added:
        text, new_pkg = bump_package_version(text, package_bump)
        summary["package_version"] = new_pkg
    pyproject.write_text(text, encoding="utf-8")

    readme = repo_root / "README.md"
    if readme.exists():
        rtext = readme.read_text(encoding="utf-8")
        readme.write_text(
            update_readme_versions(rtext, parse_supported(text)), encoding="utf-8"
        )
    return summary
