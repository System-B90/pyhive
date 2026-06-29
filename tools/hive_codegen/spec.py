"""Load Hive's OpenAPI spec and extract the parts PyHive cares about."""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .config import Config

# A spec enum description encodes member labels as lines like ``* `1` - Hanich``.
_LABEL_RE = re.compile(r"^\*\s*`(?P<value>[^`]+)`\s*-\s*(?P<label>.+)$", re.MULTILINE)


@dataclass(frozen=True)
class EnumSchema:
    name: str
    is_int: bool
    # Ordered (member_value, label-or-None) pairs as they appear in the spec.
    members: tuple[tuple[Any, str | None], ...]


@dataclass(frozen=True)
class Spec:
    version: str
    raw: dict[str, Any]
    # Real (non-noise) component schemas, name -> schema dict.
    object_schemas: dict[str, dict[str, Any]]
    enums: dict[str, EnumSchema]
    # endpoint_path -> {method -> {operationId, query_params: {name: type}}}
    endpoints: dict[str, dict[str, Any]]


def _labels_from_description(description: str) -> dict[str, str]:
    return {m["value"]: m["label"] for m in _LABEL_RE.finditer(description or "")}


def _parse_enum(name: str, schema: dict[str, Any]) -> EnumSchema:
    values = schema["enum"]
    is_int = all(isinstance(v, int) and not isinstance(v, bool) for v in values)
    labels = _labels_from_description(schema.get("description", ""))
    members = tuple((v, labels.get(str(v))) for v in values)
    return EnumSchema(name=name, is_int=is_int, members=members)


# drf-spectacular emits validation constraints (notably blacklist `pattern`
# regexes) that PyHive deliberately omits — it models payload fields as plain
# `str`/`int`. Stripping them keeps the generated types permissive and avoids
# false validation failures on real server data.
_CONSTRAINT_KEYS = frozenset(
    {
        "pattern",
        "maxLength",
        "minLength",
        "maxItems",
        "minItems",
        "maximum",
        "minimum",
        "exclusiveMaximum",
        "exclusiveMinimum",
        "multipleOf",
        "uniqueItems",
        "maxProperties",
        "minProperties",
    }
)


def _strip_constraints(node: Any) -> None:
    if isinstance(node, dict):
        for key in _CONSTRAINT_KEYS & node.keys():
            del node[key]
        for value in node.values():
            _strip_constraints(value)
    elif isinstance(node, list):
        for item in node:
            _strip_constraints(item)


def _apply_skip_fields(
    object_schemas: dict[str, dict[str, Any]], entries: tuple[str, ...]
) -> None:
    """Remove ``Schema.field`` entries entirely (declared by the curated layer)."""

    for entry in entries:
        schema_name, _, field_name = entry.partition(".")
        schema = object_schemas.get(schema_name)
        if not schema:
            continue
        (schema.get("properties") or {}).pop(field_name, None)
        if field_name in (schema.get("required") or []):
            schema["required"] = [r for r in schema["required"] if r != field_name]


def _apply_force_optional(
    object_schemas: dict[str, dict[str, Any]], entries: tuple[str, ...]
) -> None:
    """Relax ``Schema.field`` entries to optional+nullable at the spec level."""

    for entry in entries:
        schema_name, _, field_name = entry.partition(".")
        schema = object_schemas.get(schema_name)
        if not schema:
            continue
        if field_name in (schema.get("required") or []):
            schema["required"] = [r for r in schema["required"] if r != field_name]
        prop = (schema.get("properties") or {}).get(field_name)
        if prop is not None and "$ref" not in prop:
            prop["nullable"] = True


def _apply_force_nullable(
    object_schemas: dict[str, dict[str, Any]], entries: tuple[str, ...]
) -> None:
    """Mark ``Schema.field`` nullable while leaving it in ``required``."""

    for entry in entries:
        schema_name, _, field_name = entry.partition(".")
        schema = object_schemas.get(schema_name)
        if not schema:
            continue
        prop = (schema.get("properties") or {}).get(field_name)
        if prop is not None and "$ref" not in prop:
            prop["nullable"] = True


def _query_param_type(param: dict[str, Any]) -> str:
    schema = param.get("schema", {})
    if schema.get("type") == "array":
        return f"list[{schema.get('items', {}).get('type', 'str')}]"
    return schema.get("type", "str")


def load_spec(path: Path, config: Config) -> Spec:
    """Parse ``api/core.yaml`` into a :class:`Spec`."""

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    schemas: dict[str, dict[str, Any]] = raw.get("components", {}).get("schemas", {})

    object_schemas: dict[str, dict[str, Any]] = {}
    enums: dict[str, EnumSchema] = {}
    for sname, sval in schemas.items():
        if config.is_noise(sname):
            continue
        if "enum" in sval:
            enums[sname] = _parse_enum(sname, sval)
        elif sval.get("type") == "object" or "properties" in sval:
            object_schemas[sname] = copy.deepcopy(sval)

    for schema in object_schemas.values():
        _strip_constraints(schema)
    _apply_skip_fields(object_schemas, config.skip_fields)
    _apply_force_optional(object_schemas, config.force_optional)
    _apply_force_nullable(object_schemas, config.force_nullable)

    endpoints: dict[str, dict[str, Any]] = {}
    for epath, methods in (raw.get("paths") or {}).items():
        if not epath.startswith("/api/core/"):
            continue
        per_method: dict[str, Any] = {}
        for method, op in methods.items():
            if not isinstance(op, dict) or "operationId" not in op:
                continue
            params = {
                p["name"]: _query_param_type(p)
                for p in op.get("parameters", [])
                if p.get("in") == "query"
            }
            per_method[method] = {
                "operationId": op["operationId"],
                "query_params": dict(sorted(params.items())),
            }
        if per_method:
            endpoints[epath] = per_method

    version = raw.get("info", {}).get("version", "")
    return Spec(
        version=version,
        raw=raw,
        object_schemas=object_schemas,
        enums=enums,
        endpoints=dict(sorted(endpoints.items())),
    )


def filtered_spec_document(spec: Spec) -> dict[str, Any]:
    """A minimal OpenAPI doc containing only the real schemas (for dmcg input)."""

    schemas: dict[str, Any] = {}
    schemas.update(spec.object_schemas)  # already force-optional-mutated
    schemas.update({k: spec.raw["components"]["schemas"][k] for k in spec.enums})
    return {
        "openapi": spec.raw.get("openapi", "3.0.3"),
        "info": spec.raw["info"],
        "paths": {},
        "components": {"schemas": dict(sorted(schemas.items()))},
    }
