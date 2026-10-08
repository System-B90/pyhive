"""Merge the specs of every Hive release in one API generation into one spec.

A generation is a run of Hive releases with no breaking drift between them, so
each release's schemas are a superset of the previous one's. Generating one
module per generation (instead of one per release) keeps the bindings free of
near-identical copies. The merged spec is the union of its releases:

- a model has every field any release has; a field that is missing from, or
  optional in, any release that has the model is optional (``T | None = None``);
- an enum has every member any release has, newest order first;
- an endpoint has every method and query parameter any release has.

A field whose type differs between releases is breaking drift, so it can only
appear when ``hive_versions.toml`` puts two incompatible releases in one
generation. :func:`merge_specs` refuses to paper over that with a union type.
"""

from __future__ import annotations

import copy
from typing import Any

from .manifest import field_type
from .spec import EnumSchema, Spec


class GenerationConflictError(ValueError):
    """Two releases of one generation disagree on a field or enum type."""


def _merge_object_schemas(specs: list[Spec]) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    names = {name for spec in specs for name in spec.object_schemas}
    for name in sorted(names):
        present = [s for s in specs if name in s.object_schemas]
        schema = copy.deepcopy(present[-1].object_schemas[name])
        props: dict[str, Any] = schema.setdefault("properties", {})
        newest_required = set(schema.get("required", []))
        required = set(newest_required)
        for older in reversed(present[:-1]):
            old_schema = older.object_schemas[name]
            old_props = old_schema.get("properties", {})
            required &= set(old_schema.get("required", []))
            for field, prop in old_props.items():
                if field not in props:
                    props[field] = copy.deepcopy(prop)
                elif field_type(props[field]) != field_type(prop):
                    raise GenerationConflictError(
                        f"`{name}.{field}` is `{field_type(prop)}` in {older.version} "
                        f"but `{field_type(props[field])}` in {present[-1].version}"
                    )
        # Optional unless every release that has the model requires it. A
        # field the merge made optional must accept the null it now defaults to.
        for field, prop in props.items():
            in_all = all(
                field in s.object_schemas[name].get("properties", {}) for s in present
            )
            if not in_all:
                required.discard(field)
            relaxed = not in_all or field in newest_required
            if field not in required and relaxed and "$ref" not in prop:
                prop["nullable"] = True
        schema["required"] = [f for f in props if f in required]
        if not schema["required"]:
            del schema["required"]
        merged[name] = schema
    return merged


def _merge_enums(specs: list[Spec]) -> tuple[dict[str, EnumSchema], dict[str, Any]]:
    """Merged enums plus their raw schemas (datamodel-code-generator reads those)."""

    enums: dict[str, EnumSchema] = {}
    raws: dict[str, Any] = {}
    names = {name for spec in specs for name in spec.enums}
    for name in sorted(names):
        present = [s for s in specs if name in s.enums]
        newest = present[-1].enums[name]
        members = list(newest.members)
        seen = {value for value, _ in members}
        for older in reversed(present[:-1]):
            old = older.enums[name]
            if old.is_int != newest.is_int:
                raise GenerationConflictError(
                    f"enum `{name}` changes value type between {older.version} "
                    f"and {present[-1].version}"
                )
            for value, label in old.members:
                if value not in seen:
                    members.append((value, label))
                    seen.add(value)
        enums[name] = EnumSchema(
            name=name, is_int=newest.is_int, members=tuple(members)
        )
        raw = copy.deepcopy(present[-1].raw["components"]["schemas"][name])
        raw["enum"] = [value for value, _ in members]
        raw["description"] = "\n".join(
            f"* `{value}` - {label}" for value, label in members if label is not None
        )
        raws[name] = raw
    return enums, raws


def _merge_endpoints(specs: list[Spec]) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for spec in specs:  # oldest first, so the newest operationId wins
        for path, methods in spec.endpoints.items():
            target = merged.setdefault(path, {})
            for method, op in methods.items():
                params = {
                    **target.get(method, {}).get("query_params", {}),
                    **op["query_params"],
                }
                target[method] = {
                    "operationId": op["operationId"],
                    "query_params": dict(sorted(params.items())),
                }
    return dict(sorted(merged.items()))


def merge_specs(specs: list[Spec]) -> Spec:
    """Merge one generation's specs, given in release order, into one spec."""

    if not specs:
        raise ValueError("a generation needs at least one spec")
    newest = specs[-1]
    versions = tuple(s.version for s in specs)
    if len(specs) == 1:
        return Spec(
            version=newest.version,
            raw=newest.raw,
            object_schemas=newest.object_schemas,
            enums=newest.enums,
            endpoints=newest.endpoints,
            versions=versions,
        )
    enums, enum_raws = _merge_enums(specs)
    raw = copy.deepcopy({k: v for k, v in newest.raw.items() if k != "paths"})
    raw.setdefault("components", {})["schemas"] = enum_raws
    return Spec(
        version=newest.version,
        raw=raw,
        object_schemas=_merge_object_schemas(specs),
        enums=enums,
        endpoints=_merge_endpoints(specs),
        versions=versions,
    )
