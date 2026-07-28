"""
Name: subject.py
Purpose: Defines the Subject type and related functionality for the Hive API Python bindings.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from collections.abc import Iterable
from typing import TYPE_CHECKING, Annotated, Any, Self, TypeVar

from pydantic import Field, PrivateAttr

from ._generated.models import Subject as _SubjectBase

if TYPE_CHECKING:
    from ...client import HiveClient
    from .module import Module
    from .program import Program


class Subject(_SubjectBase):
    """Represents a Subject in the Hive system.

    Data fields (id, symbol, parent_program_id, color, name, ...) are inherited
    from the generated base. ``segel_brief`` is overridden as required to keep
    PyHive's established contract (the spec marks it optional).
    """

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]
    segel_brief: str
    _parent_program: "Program | None" = PrivateAttr(default=None)

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        """Deserialize a Subject from a dictionary.

        Args:
            src_dict: A dictionary containing Subject data.
            hive_client: An instance of HiveClient.

        Returns:
            A Subject instance.

        """
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)

    @property
    def parent_program(self) -> "Program":
        """Lazily load and return the parent Program.

        Returns:
            Program: The parent program instance.

        """
        if self._parent_program is None:
            self._parent_program = self.hive_client.get_program(self.parent_program_id)
        return self._parent_program

    def get_modules(self) -> Iterable["Module"]:
        """Retrieve all modules associated with this subject.

        Returns:
            Iterable[Module]: Iterable of Module instances.

        """
        return self.hive_client.get_modules(parent_subject__id=self.id)

    def get_module(self, module_name: str) -> "Module":
        """Retrieve a specific module by name within this subject.

        Args:
            module_name (str): The name of the module to retrieve.

        Returns:
            Module: The Module instance if found.

        """
        modules = list(
            self.hive_client.get_modules(
                parent_subject__id=self.id, module_name=module_name
            )
        )
        if len(modules) == 0:
            raise ValueError(
                f"Module '{module_name}' not found in subject '{self.name}'"
            )
        if len(modules) > 1:
            raise ValueError(
                f"Multiple modules named '{module_name}' found in subject '{self.name}'"
            )
        return modules[0]

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Subject):
            return False
        return self.id == value.id and self.parent_program == value.parent_program

    def __lt__(self, value: object) -> bool:
        if not isinstance(value, Subject):
            return NotImplemented
        return self.symbol < value.symbol

    def __hash__(self) -> int:
        return hash(
            (
                self.id,
                self.parent_program_id,
            )
        )

    def delete(self) -> None:
        self.hive_client.delete_subject(self.id)

    def create_module(
        self,
        name: str,
        order: int,
        segel_brief: str = "",
    ) -> "Module":
        return self.hive_client.create_module(
            name=name, order=order, segel_brief=segel_brief, parent_subject=self
        )


T = TypeVar("T", bound="Subject")
SubjectLike = TypeVar("SubjectLike", Subject, int)
