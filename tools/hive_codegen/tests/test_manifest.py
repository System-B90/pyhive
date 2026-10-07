"""Offline unit tests for hive_codegen.manifest (build_manifest, field_type)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from hive_codegen.config import Config
from hive_codegen.manifest import build_manifest, field_type
from hive_codegen.spec import EnumSchema, Spec


def _config(**overrides: object) -> Config:
    defaults: dict[str, object] = {
        "output_package": "pyhive/src/types/_generated",
        "base_class": "pyhive.src.types.core_item.HiveCoreItem",
        "noise_name_contains": (),
        "aliases": {},
        "force_optional": (),
        "force_nullable": (),
        "skip_fields": (),
        "model_to_schema": {},
        "curated_only_models": (),
        "curated_only_enums": (),
    }
    defaults.update(overrides)
    return Config(**defaults)  # type: ignore[arg-type]


def testfield_type_ref() -> None:
    assert field_type({"$ref": "#/components/schemas/User"}) == "User"


def testfield_type_combinator_wrapped_ref() -> None:
    prop = {"allOf": [{"$ref": "#/components/schemas/User"}]}
    assert field_type(prop) == "User"

    prop2 = {"oneOf": [{"$ref": "#/components/schemas/User"}]}
    assert field_type(prop2) == "User"


def testfield_type_nested_array() -> None:
    prop = {"type": "array", "items": {"type": "array", "items": {"type": "integer"}}}
    assert field_type(prop) == "list[list[integer]]"


def testfield_type_array_of_ref() -> None:
    prop = {"type": "array", "items": {"$ref": "#/components/schemas/User"}}
    assert field_type(prop) == "list[User]"


def testfield_type_bare_type() -> None:
    assert field_type({"type": "string"}) == "string"
    assert field_type({}) == "any"


def test_build_manifest_deterministic_and_covers_fields() -> None:
    spec = Spec(
        version="7.2.0",
        raw={},
        object_schemas={
            "Exercise": {
                "required": ["id"],
                "properties": {
                    "id": {"type": "integer"},
                    "checker": {"$ref": "#/components/schemas/User"},
                },
            }
        },
        enums={
            "StatusEnum": EnumSchema(
                name="StatusEnum", is_int=False, members=(("active", "Active"),)
            )
        },
        endpoints={
            "/api/core/exercises/": {"get": {"operationId": "x", "query_params": {}}}
        },
    )
    config = _config(
        aliases={"checker": "checker_id"},
        model_to_schema={"ExerciseCurated": "Exercise"},
    )

    manifest = build_manifest(spec, config)

    assert manifest["version"] == "7.2.0"
    assert manifest["models"]["Exercise"]["curated_model"] == "ExerciseCurated"
    fields = manifest["models"]["Exercise"]["fields"]
    assert fields["id"] == {
        "wire": "id",
        "type": "integer",
        "required": True,
        "nullable": False,
    }
    assert fields["checker_id"] == {
        "wire": "checker",
        "type": "User",
        "required": False,
        "nullable": False,
    }
    assert manifest["enums"]["StatusEnum"]["members"] == {"ACTIVE": "active"}
    assert manifest["endpoints"] == spec.endpoints
