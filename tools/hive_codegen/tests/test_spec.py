"""Offline unit tests for hive_codegen.spec (load_spec + mutation helpers)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from hive_codegen.config import Config
from hive_codegen.spec import load_spec

FIXTURE_YAML = """\
openapi: 3.0.3
info:
  title: Hive API
  version: 7.2.0
paths:
  /api/core/exercises/:
    get:
      operationId: exercises_list
      parameters:
        - name: name
          in: query
          schema:
            type: string
        - name: ids
          in: query
          schema:
            type: array
            items:
              type: integer
        - name: page
          in: query
          schema:
            type: integer
  /api/other/things/:
    get:
      operationId: things_list
      parameters: []
components:
  schemas:
    Exercise:
      type: object
      required: [id, name]
      properties:
        id:
          type: integer
        name:
          type: string
          maxLength: 100
        note:
          type: string
          nullable: false
        secret:
          type: string
    StatusEnum:
      type: string
      description: |
        * `active` - Active
        * `done` - Done
      enum: [active, done]
    ExerciseRequest:
      type: object
      properties:
        name:
          type: string
"""


def _config(**overrides: object) -> Config:
    defaults: dict[str, object] = {
        "output_package": "pyhive/src/types/_generated",
        "base_class": "pyhive.src.types.core_item.HiveCoreItem",
        "noise_name_contains": ("Request",),
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


def test_load_spec_classifies_enum_vs_object(tmp_path: Path) -> None:
    path = tmp_path / "core.yaml"
    path.write_text(FIXTURE_YAML, encoding="utf-8")
    spec = load_spec(path, _config())

    assert "Exercise" in spec.object_schemas
    assert "StatusEnum" in spec.enums
    assert spec.enums["StatusEnum"].is_int is False
    assert spec.enums["StatusEnum"].members == (
        ("active", "Active"),
        ("done", "Done"),
    )


def test_load_spec_skips_noise_names(tmp_path: Path) -> None:
    path = tmp_path / "core.yaml"
    path.write_text(FIXTURE_YAML, encoding="utf-8")
    spec = load_spec(path, _config())

    assert "ExerciseRequest" not in spec.object_schemas


def test_load_spec_strips_constraints(tmp_path: Path) -> None:
    path = tmp_path / "core.yaml"
    path.write_text(FIXTURE_YAML, encoding="utf-8")
    spec = load_spec(path, _config())

    assert "maxLength" not in spec.object_schemas["Exercise"]["properties"]["name"]


def test_load_spec_skip_fields_removes_property_and_required(tmp_path: Path) -> None:
    path = tmp_path / "core.yaml"
    path.write_text(FIXTURE_YAML, encoding="utf-8")
    spec = load_spec(path, _config(skip_fields=("Exercise.secret",)))

    assert "secret" not in spec.object_schemas["Exercise"]["properties"]


def test_load_spec_force_optional_relaxes_required_and_nullable(tmp_path: Path) -> None:
    path = tmp_path / "core.yaml"
    path.write_text(FIXTURE_YAML, encoding="utf-8")
    spec = load_spec(path, _config(force_optional=("Exercise.name",)))

    schema = spec.object_schemas["Exercise"]
    assert "name" not in schema["required"]
    assert schema["properties"]["name"]["nullable"] is True


def test_load_spec_force_nullable_keeps_required(tmp_path: Path) -> None:
    path = tmp_path / "core.yaml"
    path.write_text(FIXTURE_YAML, encoding="utf-8")
    spec = load_spec(path, _config(force_nullable=("Exercise.id",)))

    schema = spec.object_schemas["Exercise"]
    assert "id" in schema["required"]
    assert schema["properties"]["id"]["nullable"] is True


def test_load_spec_endpoint_extraction_excludes_non_core_paths(tmp_path: Path) -> None:
    path = tmp_path / "core.yaml"
    path.write_text(FIXTURE_YAML, encoding="utf-8")
    spec = load_spec(path, _config())

    assert "/api/other/things/" not in spec.endpoints
    assert "/api/core/exercises/" in spec.endpoints


def test_load_spec_endpoint_query_param_types(tmp_path: Path) -> None:
    path = tmp_path / "core.yaml"
    path.write_text(FIXTURE_YAML, encoding="utf-8")
    spec = load_spec(path, _config())

    params = spec.endpoints["/api/core/exercises/"]["get"]["query_params"]
    assert params == {"ids": "list[integer]", "name": "string", "page": "integer"}
    # sorted output
    assert list(params.keys()) == sorted(params.keys())


@pytest.mark.parametrize(
    ("value", "label"),
    [(1, "One"), (2, "Two")],
)
def test_int_enum_detection(tmp_path: Path, value: int, label: str) -> None:
    yaml_doc = f"""\
openapi: 3.0.3
info:
  title: Hive API
  version: 1.0.0
paths: {{}}
components:
  schemas:
    Kind:
      type: integer
      description: "* `{value}` - {label}"
      enum: [{value}]
"""
    path = tmp_path / "core.yaml"
    path.write_text(yaml_doc, encoding="utf-8")
    spec = load_spec(path, _config())

    assert spec.enums["Kind"].is_int is True
