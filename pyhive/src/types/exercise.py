"""
Name: exercise.py
Purpose: Model for exercises in course modules.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from collections.abc import Generator, Iterable
from typing import TYPE_CHECKING, Annotated, Any, TypeVar

from typing_extensions import Self

from pydantic import Field, PrivateAttr

from ._generated.models import Exercise as _ExerciseBase

if TYPE_CHECKING:
    from ...client import HiveClient
    from .assignment import Assignment
    from .module import Module
    from .subject import Subject


class Exercise(_ExerciseBase):
    """Represents an exercise in a course module.

    Data fields are inherited from the generated base; this layer adds the
    ``hive_client`` binding, lazy parent relations and convenience helpers.
    """

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]

    _parent_module: "Module | None" = PrivateAttr(default=None)
    _parent_subject: "Subject | None" = PrivateAttr(default=None)

    @property
    def parent_module(self) -> "Module":
        """Lazily load the module this exercise belongs to."""
        if self._parent_module is None:
            self._parent_module = self.hive_client.get_module(self.parent_module_id)
        return self._parent_module

    @property
    def parent_subject(self) -> "Subject":
        """Lazily load the subject this exercise belongs to."""
        if self._parent_subject is None:
            self._parent_subject = self.hive_client.get_subject(self.parent_subject_id)
        return self._parent_subject

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        """Deserializes Exercise from dictionary payload."""
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Exercise):
            return False
        return self.id == value.id and self.parent_module_id == value.parent_module_id

    def __lt__(self, value: object) -> bool:
        if not isinstance(value, Exercise):
            return NotImplemented
        return self.order < value.order

    def __hash__(self) -> int:
        return hash((self.id, self.parent_module_id, self.parent_subject_id))

    def get_assignments(self) -> Iterable["Assignment"]:
        """Fetch all assignments associated with this exercise."""
        return self.hive_client.get_assignments(
            exercise__id=self.id,
            exercise__parent_module__id=self.parent_module_id,
            exercise__parent_module__parent_subject__id=self.parent_subject_id,
        )

    def iter_assignments(self) -> Generator["Assignment", None, None]:
        """Allow iteration over this Exercise to yield its assignments."""
        yield from self.get_assignments()

    def delete(self) -> None:
        """Deletes the exercise using the underlying HiveClient."""
        self.hive_client.delete_exercise(self)


ExerciseLike = TypeVar("ExerciseLike", Exercise, int)
