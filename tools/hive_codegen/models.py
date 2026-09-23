"""Emit ``_generated/models.py`` by driving datamodel-code-generator.

We use datamodel-code-generator (the engine) for robust OpenAPI -> Pydantic v2
type resolution, then post-process its output so the result matches PyHive
conventions:

- every model inherits ``HiveCoreItem`` (via ``--base-class``);
- FK / reserved fields are renamed with ``Field(alias=...)`` (via ``--aliases``);
- enum classes are replaced by an import from the hand-controlled ``enums.py``;
- ``AwareDatetime`` is normalised to ``datetime.datetime`` (PyHive accepts the
  server's datetimes verbatim).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

from .config import Config
from .spec import Spec, filtered_spec_document

_TOP_CLASS_RE = re.compile(r"^class\s+(\w+)\b", re.MULTILINE)


def _run_dmcg(
    spec_doc_path: Path, aliases_path: Path, base_class: str, out_path: Path
) -> None:
    cmd = [
        sys.executable,
        "-m",
        "datamodel_code_generator",
        "--input",
        str(spec_doc_path),
        "--input-file-type",
        "openapi",
        "--output-model-type",
        "pydantic_v2.BaseModel",
        "--base-class",
        base_class,
        "--aliases",
        str(aliases_path),
        "--use-annotated",
        "--use-field-description",
        "--field-constraints",
        "--collapse-root-models",
        "--strict-nullable",
        "--target-python-version",
        "3.11",
        "--formatters",
        "black",
        "--output",
        str(out_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def _split_top_level_blocks(body: str) -> list[str]:
    """Split a module body into top-level class blocks (header stripped already)."""

    indices = [m.start() for m in _TOP_CLASS_RE.finditer(body)]
    if not indices:
        return [body] if body.strip() else []
    blocks = []
    for i, start in enumerate(indices):
        end = indices[i + 1] if i + 1 < len(indices) else len(body)
        blocks.append(body[start:end])
    return blocks


def _transform_header(header: str, drop_pydantic: set[str]) -> str:
    """Preserve dmcg's imports but normalise datetime, ordering and dead imports.

    ``from __future__`` must lead; dmcg's banner comments and now-unused ``enum``
    imports (enum classes are stripped) are dropped; ``AwareDatetime`` becomes a
    plain ``datetime`` import; ``drop_pydantic`` names are removed from the
    pydantic import (types normalised away during post-processing).
    """

    other: list[str] = []
    has_datetime_import = False
    for ln in header.splitlines():
        stripped = ln.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("from __future__"):
            continue  # re-emitted explicitly first
        if stripped.startswith("from enum import"):
            continue  # enums live in enums.py
        if stripped.startswith("from pydantic import"):
            names = [n.strip() for n in stripped.split("import", 1)[1].split(",")]
            names = [n for n in names if n and n not in drop_pydantic]
            if not names:
                continue
            stripped = f"from pydantic import {', '.join(names)}"
        if stripped.startswith("from datetime import") and "datetime" in stripped:
            has_datetime_import = True
        other.append(stripped)
    if not has_datetime_import:
        other.insert(0, "from datetime import datetime")
    return "from __future__ import annotations\n\n" + "\n".join(other)


def _postprocess(raw: str, spec: Spec) -> str:
    # dmcg renders an import header then the class blocks; split at the first class.
    first = _TOP_CLASS_RE.search(raw)
    header_raw = raw[: first.start()] if first else ""
    body = raw[first.start() :] if first else raw

    # Collapse primitive RootModel wrappers (e.g. a constrained-string `Choice`)
    # back to the primitive, matching PyHive's plain `str`/`int` fields.
    rootmodel_re = re.compile(r"^class\s+(\w+)\(RootModel\[(\w+)\]\)", re.MULTILINE)
    rootmodels = {m.group(1): m.group(2) for m in rootmodel_re.finditer(body)}

    enum_names = set(spec.enums)
    kept_blocks = []
    for block in _split_top_level_blocks(body):
        name = _TOP_CLASS_RE.match(block).group(1)
        if name in enum_names or name in rootmodels:
            continue  # enums come from enums.py; root models collapse to primitives
        kept_blocks.append(block.rstrip() + "\n")

    models_src = "\n\n".join(kept_blocks).replace("AwareDatetime", "datetime")
    for wrapper, inner in rootmodels.items():
        models_src = re.sub(rf"\b{wrapper}\b", inner, models_src)
    # PyHive treats emails/URLs as plain strings (no email-validator dependency).
    models_src = re.sub(r"\bEmailStr\b", "str", models_src)
    models_src = re.sub(r"\bAnyUrl\b", "str", models_src)

    used_enums = {e for e in enum_names if re.search(rf"\b{e}\b", models_src)}

    docstring = (
        '"""Hive API model bases — AUTO-GENERATED by tools/hive_codegen. Do not edit.\n\n'
        f"Generated from Hive OpenAPI spec version {spec.version}.\n"
        "The curated layer (pyhive/src/types/*.py) subclasses these bases.\n"
        '"""'
    )
    drop_pydantic = {"AwareDatetime", "EmailStr", "AnyUrl"}
    if "RootModel" not in models_src:
        drop_pydantic.add("RootModel")
    header = _transform_header(header_raw, drop_pydantic)
    if used_enums:
        header += f"\nfrom .enums import {', '.join(sorted(used_enums))}"

    return f"{docstring}\n{header}\n\n\n{models_src.lstrip(chr(10))}\n"


def render_models_module(spec: Spec, config: Config) -> str:
    """Generate the ``models.py`` source as a string."""

    aliases = dict(config.aliases)
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        spec_doc = tdp / "filtered.yaml"
        spec_doc.write_text(
            yaml.safe_dump(filtered_spec_document(spec), sort_keys=False),
            encoding="utf-8",
        )
        aliases_path = tdp / "aliases.json"
        aliases_path.write_text(json.dumps(aliases), encoding="utf-8")
        out_path = tdp / "models.py"
        _run_dmcg(spec_doc, aliases_path, config.base_class, out_path)
        raw = out_path.read_text(encoding="utf-8")
    return _postprocess(raw, spec)
