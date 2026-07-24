"""Build the drift-detection manifest from a parsed spec."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import Config
from .enums import member_name
from .spec import Spec

MANIFEST_NAME = "manifest.json"


def _type_of(prop: dict[str, Any]) -> str:
    if "$ref" in prop:
        return prop["$ref"].rsplit("/", 1)[-1]
    for combinator in ("allOf", "oneOf", "anyOf"):
        if prop.get(combinator):
            inner = prop[combinator][0]
            if "$ref" in inner:
                return inner["$ref"].rsplit("/", 1)[-1]
    t = prop.get("type", "any")
    if t == "array":
        items = prop.get("items", {})
        return f"list[{_type_of(items)}]"
    return t


def build_manifest(spec: Spec, config: Config) -> dict[str, Any]:
    """Construct the manifest dict (deterministic — no timestamps)."""

    enums: dict[str, Any] = {}
    for name in sorted(spec.enums):
        e = spec.enums[name]
        members = {
            member_name(value, label, e.is_int): value for value, label in e.members
        }
        enums[name] = {"is_int": e.is_int, "members": members}

    models: dict[str, Any] = {}
    for sname in sorted(spec.object_schemas):
        schema = spec.object_schemas[sname]
        required = set(schema.get("required", []))
        props = schema.get("properties", {})
        fields: dict[str, Any] = {}
        for wire, prop in props.items():
            py_name = config.aliases.get(wire, wire)
            fields[py_name] = {
                "wire": wire,
                "type": _type_of(prop),
                "required": wire in required,
                "nullable": bool(prop.get("nullable", False)),
            }
        models[sname] = {
            "curated_model": config.schema_to_model.get(sname, sname),
            "fields": dict(sorted(fields.items())),
        }

    return {
        "version": spec.version,
        "curated_only": {
            "models": list(config.curated_only_models),
            "enums": list(config.curated_only_enums),
        },
        "enums": enums,
        "models": models,
        "endpoints": spec.endpoints,
    }


def write_manifest(manifest: dict[str, Any], output_dir: Path) -> Path:
    path = output_dir / MANIFEST_NAME
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_manifest(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
