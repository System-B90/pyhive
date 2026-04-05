"""
Name: form_field.py
Purpose: Model definition for a form field used in questionnaires or structured input forms within Hive.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Any, Self, TypeVar

from pydantic import Field, PrivateAttr

from .core_item import HiveCoreItem
from .enums.form_field_type_enum import FormFieldTypeEnum

if TYPE_CHECKING:
    from ...client import HiveClient
    from .program import Class


class FormField(HiveCoreItem):
    """Represents a single field in a dynamic form.

    Attributes:
        id: Field ID.
        name: Name of the field.
        type_: Field type (e.g., text, number, multiple).
        order: Position of the field in the form.
        required: Whether this field must be filled out.
        staff_responses: Whether staff members can respond.
        hanich_responses: Whether students can respond.
        has_value: Whether the field currently holds a value.
        segel_only: Whether the field is visible only to Segel (staff).
        description: Optional description of the field.
        lower_limit: Optional lower numeric limit.
        upper_limit: Optional upper numeric limit.
        choices: Optional list of string choices (for multiple/multiResponse).
        metadata: Additional arbitrary metadata for the field.
        groups: Optional list of group IDs the field is associated with.

    """

    hive_client: "HiveClient" = Field(exclude=True, repr=False)
    id: int
    name: str
    type_: FormFieldTypeEnum = Field(alias="type")
    order: int
    required: bool
    staff_responses: bool
    hanich_responses: bool
    has_value: bool
    segel_only: bool
    description: str | None = Field(default=None)
    lower_limit: int | None = Field(default=None)
    upper_limit: int | None = Field(default=None)
    choices: list[str] | None = Field(default=None)
    metadata: Any = Field(default=None)
    group_ids: list[int] | None = Field(default=None, alias="groups")
    _groups: "list[Class] | None" = PrivateAttr(default=None)

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)

    @property
    def groups(self) -> list["Class"]:
        """Return the list of Classes which this field is relevant to."""
        if self.group_ids is None:
            return []
        if self._groups is None:
            self._groups = [
                self.hive_client.get_class(group_id) for group_id in self.group_ids
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
