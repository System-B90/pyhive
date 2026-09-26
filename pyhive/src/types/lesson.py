"""
Name: lesson.py
Purpose: Model for schedule lessons in the Hive system.
Created: 2026-08-23
Author: Michael K. Steinberg
"""

from collections.abc import Iterable
from typing import TYPE_CHECKING, Annotated, Any, TypeVar

from pydantic import Field, PrivateAttr
from typing_extensions import Self

from ._generated.models import Lesson as _LessonBase

if TYPE_CHECKING:
    from ...client import HiveClient
    from .lesson_rule import LessonRule
    from .module import Module


class Lesson(_LessonBase):
    """A schedule lesson attached to a module. Data fields are inherited."""

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]

    _module: "Module | None" = PrivateAttr(default=None)

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)

    @property
    def module(self) -> "Module":
        """Lazily load and return the lesson's parent module."""
        if self._module is None:
            self._module = self.hive_client.get_module(self.module_id)
        return self._module

    def get_rules(self) -> Iterable["LessonRule"]:
        """Yield all queue rules configured for this lesson."""
        return self.hive_client.get_lesson_rules(lesson=self)


T = TypeVar("T", bound="Lesson")
