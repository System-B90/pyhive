"""Produce Hive's ``core.yaml`` for an exact release by running its own backend.

Hive's committed ``api/core.yaml`` is only refreshed when a developer remembers
to run ``./manage_hive.py --env dev generate_api``, and at several tags it lags
the backend it ships with: v7.3.0's file still types Lesson/Event ids as
integers although the 7.3.0 server uses UUIDs, and v6.4.0 / v7.2.0 are byte-for-
byte their predecessors apart from the version line. So this module does what
``generate_api`` does, per tag and without a running stack: it builds that
tag's ``core`` image and runs ``manage.py spectacular`` inside it.

The Hive checkout is only read (``git archive``), never modified, and images
are tagged ``pyhive-spec/*`` so they never replace a developer's ``hive/*``.
"""

from __future__ import annotations

import re
import subprocess
import tarfile
import tempfile
from io import BytesIO
from pathlib import Path

IMAGE_PREFIX = "pyhive-spec"
_FROM_BASE_RE = re.compile(r"(?m)^FROM\s+hive/core[-_]base\b.*$")
_FROM_RE = re.compile(r"(?m)^FROM\s+.*$")
# Older tags build on Debian releases whose apt repos have since moved to
# archive.debian.org, so their unmodified `apt-get update` now fails.
_EOL_APT_FIX = (
    'RUN . /etc/os-release; case "$VERSION_CODENAME" in buster|bullseye) '
    "sed -i 's|deb.debian.org|archive.debian.org|g' /etc/apt/sources.list;; esac"
)
# spectacular writes the file, then we cat it: Django may log to stdout first.
_SPECTACULAR = (
    "python -Xfrozen_modules=off manage.py spectacular --file /tmp/core.yaml "
    "1>&2 && cat /tmp/core.yaml"
)


def _run(cmd: list[str], *, capture: bool = False) -> bytes:
    result = subprocess.run(cmd, check=True, capture_output=capture)
    return result.stdout or b""


def _export_tag(hive_repo: Path, tag: str, dest: Path) -> None:
    """Write ``core/`` and ``.env`` as they are at ``tag`` into ``dest``."""

    archive = _run(
        ["git", "-C", str(hive_repo), "archive", "--format=tar", tag, "core", ".env"],
        capture=True,
    )
    with tarfile.open(fileobj=BytesIO(archive)) as tar:
        tar.extractall(dest, filter="data")


def _patch_dockerfiles(core: Path, base_image: str, tag: str) -> None:
    dockerfile = core / "Dockerfile"
    text = dockerfile.read_text(encoding="utf-8")
    if not _FROM_BASE_RE.search(text):
        raise RuntimeError(f"{tag}: core/Dockerfile does not build FROM hive/core-base")
    # The base image name changed over time (core_base -> core-base); point
    # whichever spelling this tag uses at our private tag instead.
    dockerfile.write_text(
        _FROM_BASE_RE.sub(f"FROM {base_image}", text), encoding="utf-8"
    )
    base = core / "base.Dockerfile"
    base.write_text(
        _FROM_RE.sub(
            lambda m: f"{m.group(0)}\n{_EOL_APT_FIX}",
            base.read_text(encoding="utf-8"),
        ),
        encoding="utf-8",
    )


def build_core_image(hive_repo: Path, tag: str, workdir: Path) -> str:
    """Build ``tag``'s core image and return its name."""

    version = tag.removeprefix("v")
    _export_tag(hive_repo, tag, workdir)
    core = workdir / "core"
    base_image = f"{IMAGE_PREFIX}/core-base:{version}"
    core_image = f"{IMAGE_PREFIX}/core:{version}"
    _patch_dockerfiles(core, base_image, tag)
    base_cmd = ["docker", "build", "-q", "-f", str(core / "base.Dockerfile")]
    _run([*base_cmd, "-t", base_image, str(core)])
    _run(["docker", "build", "-q", "-t", core_image, str(core)])
    return core_image


def generate_spec(image: str, env_file: Path) -> bytes:
    """Run drf-spectacular inside ``image`` and return the YAML it produced."""

    return _run(
        [
            "docker",
            "run",
            "--rm",
            "--network=none",
            "--env-file",
            str(env_file),
            "-e",
            "DJANGO_SETTINGS_MODULE=core.settings",
            "-e",
            "OTEL_SDK_DISABLED=true",
            "--entrypoint",
            "sh",
            image,
            "-c",
            _SPECTACULAR,
        ],
        capture=True,
    )


def extract_spec(hive_repo: Path, tag: str, out: Path) -> Path:
    """Build ``tag`` and write its generated spec to ``out``."""

    with tempfile.TemporaryDirectory(prefix=f"hive-{tag}-") as tmp:
        workdir = Path(tmp)
        image = build_core_image(hive_repo, tag, workdir)
        spec = generate_spec(image, workdir / ".env")
    if not spec.lstrip().startswith(b"openapi:"):
        raise RuntimeError(f"{tag}: spectacular did not return an OpenAPI document")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(spec)
    return out
