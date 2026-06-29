"""Load and represent ``codegen.toml``."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_NAME = "codegen.toml"


@dataclass(frozen=True)
class Config:
    """Parsed codegen configuration."""

    output_package: str
    base_class: str
    noise_name_contains: tuple[str, ...]
    aliases: dict[str, str]
    force_optional: tuple[str, ...]
    force_nullable: tuple[str, ...]
    skip_fields: tuple[str, ...]
    model_to_schema: dict[str, str]
    curated_only_models: tuple[str, ...]
    curated_only_enums: tuple[str, ...]
    repo_root: Path = field(default_factory=Path.cwd)

    @property
    def output_dir(self) -> Path:
        return self.repo_root / self.output_package

    @property
    def schema_to_model(self) -> dict[str, str]:
        return {schema: model for model, schema in self.model_to_schema.items()}

    def is_noise(self, schema_name: str) -> bool:
        return any(token in schema_name for token in self.noise_name_contains)


def load_config(path: Path | None = None, repo_root: Path | None = None) -> Config:
    """Load configuration from ``codegen.toml`` next to this package."""

    cfg_path = path or (Path(__file__).resolve().parent / CONFIG_NAME)
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    out = data.get("output", {})
    spec = data.get("spec", {})
    curated = data.get("curated_only", {})
    return Config(
        output_package=out["package"],
        base_class=out["base_class"],
        noise_name_contains=tuple(spec.get("noise_name_contains", [])),
        aliases=dict(data.get("aliases", {})),
        force_optional=tuple(spec.get("force_optional", {}).get("fields", [])),
        force_nullable=tuple(spec.get("force_nullable", {}).get("fields", [])),
        skip_fields=tuple(spec.get("skip_fields", {}).get("fields", [])),
        model_to_schema=dict(data.get("models", {})),
        curated_only_models=tuple(curated.get("models", [])),
        curated_only_enums=tuple(curated.get("enums", [])),
        repo_root=(repo_root or Path.cwd()).resolve(),
    )
