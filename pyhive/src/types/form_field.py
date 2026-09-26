"""
Name: form_field.py
Purpose: Model definition for a form field used in questionnaires or structured input forms within Hive.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Annotated, Any, TypeVar

from pydantic import Field, PrivateAttr
from typing_extensions import Self

from ._generated.models import FormField as _FormFieldBase

if TYPE_CHECKING:
    from ...client import HiveClient
    from .program import Class


class FormField(_FormFieldBase):
    """Represents a single field in a dynamic form. Data fields are inherited
    from the generated base."""

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]

    _groups: "list[Class] | None" = PrivateAttr(default=None)

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)

    @property
    def groups(self) -> list["Class"]:
        """Return the list of Classes which this field is relevant to."""
        group_ids = self.group_ids or []
        if not group_ids:
            return []
        if self._groups is None:
            self._groups = [
                self.hive_client.get_class(group_id) for group_id in group_ids
            ]
        return self._groups

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, FormField):
            return False
        return self.id == value.id

    def __lt__(self, value: object) -> bool:
        if not isinstance(value, FormField):
            return NotImplemented
        return self.order < value.order

    def __hash__(self) -> int:
        return hash((self.id,))


T = TypeVar("T", bound="FormField")
