"""
Name: program.py
Purpose: Model definition for the Hive Program entity.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from collections.abc import Iterable
from typing import TYPE_CHECKING, Annotated, Any, TypeVar

from typing_extensions import Self

from pydantic import Field, PrivateAttr

from ._generated.models import Program as _ProgramBase
from .subject import Subject

if TYPE_CHECKING:
    from ...client import HiveClient
    from .class_ import Class
    from .user import User


class Program(_ProgramBase):
    """Course Program entity. Data fields are inherited from the generated base.

    ``hanich_work_name`` is retained here because it was dropped from the live
    spec; PyHive keeps exposing it for backward compatibility.
    """

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]
    hanich_work_name: bool | None = Field(default=None)

    _checker: "User | None" = PrivateAttr(default=None)
    _default_class: "Class | None" = PrivateAttr(default=None)

    def __str__(self) -> str:
        return f"<Program[{self.id}] {self.name}>"

    @property
    def checker(self) -> "User":
        """
        Lazily loads and returns the checker (staff member).

        Returns:
            User: The associated checker entity.
        """
        if self._checker is None:
            self._checker = self.hive_client.get_user(self.checker_id)
        return self._checker

    @property
    def default_class(self) -> "Class | None":
        """
        Lazily loads the default class, if set.

        Returns:
            Class | None: The associated default class entity, or None if not set.
        """
        if self._default_class is None and self.default_class_id is not None:
            self._default_class = self.hive_client.get_class(self.default_class_id)
        return self._default_class

    def get_subjects(self) -> Iterable[Subject]:
        """
        Returns all subjects belonging to this program.

        Returns:
            Iterable[Subject]: An iterable collection of subject models.
        """
        return self.hive_client.get_subjects(parent_program__id__in=[self.id])

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        """
        Deserializes a Program instance from a dictionary payload.

        Args:
            src_dict (dict[str, Any]): The raw dictionary from the API response.
            hive_client (HiveClient): The client instance for deferred network operations.

        Returns:
            Self: An instantiated and validated Program model.
        """
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Program):
            return False
        return (
            self.id == value.id
            and self.checker_id == value.checker_id
            and self.name == value.name
        )

    def delete(self) -> None:
        """
        Deletes the program using the underlying HiveClient.

        Returns:
            None
        """
        self.hive_client.delete_program(self.id)

    def create_subject(
        self,
        symbol: str,
        name: str,
        color: str,
        segel_brief: str = "",
    ) -> Subject:
        """
        Creates a new subject associated with this program.

        Args:
            symbol (str): The subject's symbolic identifier.
            name (str): The display name of the subject.
            color (str): The UI color code for the subject.
            segel_brief (str, optional): Briefing context for the staff. Defaults to "".

        Returns:
            Subject: The newly created subject model.
        """
        return self.hive_client.create_subject(
            symbol=symbol, name=name, program=self, color=color, segel_brief=segel_brief
        )


ProgramLike = TypeVar("ProgramLike", Program, int)
