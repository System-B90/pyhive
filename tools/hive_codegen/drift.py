"""Classify the difference between two manifests as additive or breaking.

ADDITIVE changes are safe to auto-merge: new models, new optional fields, new
enums/members, new endpoints or query params. BREAKING changes require a human:
removed or retyped fields, removed models/enums/members, removed endpoints or
params. New *required* fields are reported as additive-with-note (they parse
fine on read but may need attention for create payloads).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DriftReport:
    from_version: str | None
    to_version: str
    additive: list[str] = field(default_factory=list)
    breaking: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def has_breaking(self) -> bool:
        return bool(self.breaking)

    @property
    def is_empty(self) -> bool:
        return not (self.additive or self.breaking or self.notes)

    def to_markdown(self) -> str:
        lines = [
            f"### Hive API drift: `{self.from_version or '∅'}` → `{self.to_version}`",
            "",
        ]
        if self.is_empty:
            lines.append("_No schema changes detected._")
            return "\n".join(lines)
        if self.breaking:
            lines.append(
                f"#### ⛔ Breaking ({len(self.breaking)}) — manual review required"
            )
            lines += [f"- {item}" for item in self.breaking]
            lines.append("")
        if self.additive:
            lines.append(
                f"#### ✅ Additive ({len(self.additive)}) — safe to auto-merge"
            )
            lines += [f"- {item}" for item in self.additive]
            lines.append("")
        if self.notes:
            lines.append(f"#### ℹ️ Notes ({len(self.notes)})")
            lines += [f"- {item}" for item in self.notes]
        return "\n".join(lines)


def _diff_enums(old: dict[str, Any], new: dict[str, Any], r: DriftReport) -> None:
    for name in new.keys() - old.keys():
        r.additive.append(f"New enum `{name}` ({len(new[name]['members'])} members)")
    for name in old.keys() - new.keys():
        r.breaking.append(f"Removed enum `{name}`")
    for name in old.keys() & new.keys():
        om, nm = old[name]["members"], new[name]["members"]
        for member in nm.keys() - om.keys():
            r.additive.append(f"Enum `{name}`: new member `{member}` = {nm[member]!r}")
        for member in om.keys() - nm.keys():
            r.breaking.append(f"Enum `{name}`: removed member `{member}`")
        if old[name]["is_int"] != new[name]["is_int"]:
            r.breaking.append(f"Enum `{name}`: value type changed (int<->str)")


def _diff_models(old: dict[str, Any], new: dict[str, Any], r: DriftReport) -> None:
    for name in new.keys() - old.keys():
        r.additive.append(f"New model `{name}`")
    for name in old.keys() - new.keys():
        r.breaking.append(f"Removed model `{name}`")
    for name in old.keys() & new.keys():
        of, nf = old[name]["fields"], new[name]["fields"]
        for fname in nf.keys() - of.keys():
            if nf[fname]["required"]:
                r.notes.append(
                    f"Model `{name}`: new required field `{fname}` "
                    f"({nf[fname]['type']}) — review create payloads"
                )
            else:
                r.additive.append(
                    f"Model `{name}`: new field `{fname}` ({nf[fname]['type']})"
                )
        for fname in of.keys() - nf.keys():
            r.breaking.append(f"Model `{name}`: removed field `{fname}`")
        for fname in of.keys() & nf.keys():
            if of[fname]["type"] != nf[fname]["type"]:
                r.breaking.append(
                    f"Model `{name}`: field `{fname}` type "
                    f"`{of[fname]['type']}` → `{nf[fname]['type']}`"
                )


def _diff_endpoints(old: dict[str, Any], new: dict[str, Any], r: DriftReport) -> None:
    for path in new.keys() - old.keys():
        r.additive.append(f"New endpoint `{path}`")
    for path in old.keys() - new.keys():
        r.breaking.append(f"Removed endpoint `{path}`")
    for path in old.keys() & new.keys():
        for method in new[path].keys() - old[path].keys():
            r.additive.append(f"Endpoint `{path}`: new method `{method.upper()}`")
        for method in old[path].keys() - new[path].keys():
            r.breaking.append(f"Endpoint `{path}`: removed method `{method.upper()}`")
        for method in old[path].keys() & new[path].keys():
            op, npr = (
                old[path][method]["query_params"],
                new[path][method]["query_params"],
            )
            for param in npr.keys() - op.keys():
                r.additive.append(
                    f"`{method.upper()} {path}`: new query param `{param}`"
                )
            for param in op.keys() - npr.keys():
                r.breaking.append(
                    f"`{method.upper()} {path}`: removed query param `{param}`"
                )


def classify(old: dict[str, Any] | None, new: dict[str, Any]) -> DriftReport:
    """Compare two manifests and classify the changes."""

    report = DriftReport(
        from_version=(old or {}).get("version"),
        to_version=new["version"],
    )
    if old is None:
        report.notes.append("No previous manifest — first generation.")
        return report
    _diff_enums(old.get("enums", {}), new.get("enums", {}), report)
    _diff_models(old.get("models", {}), new.get("models", {}), report)
    _diff_endpoints(old.get("endpoints", {}), new.get("endpoints", {}), report)
    return report
