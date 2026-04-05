"""
Name: exercise.py
Purpose: Model for exercises in course modules.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from collections.abc import Generator, Iterable
from typing import Annotated,TYPE_CHECKING, Any, Self, TypeVar

from pydantic import Field, PrivateAttr

from .core_item import HiveCoreItem
from .enums.exercise_patbas_enum import PatbasEnum
from .enums.exercise_preview_types import ExercisePreviewTypes
from .enums.sync_status_enum import SyncStatusEnum

if TYPE_CHECKING:
    from ...client import HiveClient
    from .assignment import Assignment
    from .module import Module
    from .subject import Subject


class Exercise(HiveCoreItem):
    """
    Represents an exercise in a course module.

    Attributes:
        id: Unique exercise ID.
        name: Exercise name.
        parent_module_id: ID of the module the exercise belongs to.
        parent_subject_id: ID of the subject the exercise belongs to.
        parent_module_name: Name of the module.
        parent_subject_symbol: Symbol of the subject.
        parent_subject_color: Color tag of the subject.
        download: Whether the exercise is downloadable.
        preview: The preview method.
        parent_subject_name: Name of the subject.
        parent_module_order: Display order of the module.
        order: Display order of the exercise.
        tags: List of tag strings.
        patbas: PATBAS mode.
        sync_status: Synchronization status.
        sync_message: Optional sync error message.
        segel_path: Path to the exercise on the staff network.
        patbas_preview: Optional preview type for PATBAS.
        patbas_download: Whether PATBAS allows download.
        is_lecture: Whether this is a lecture.
        style: Optional style.
        on_creation_data: Optional metadata used on creation.
        autocheck_tag: Optional tag for auto-checking.
        autodone: Whether it can be automatically marked done.
        expected_duration: Optional string representing duration.
        segel_brief: Optional brief description.
    """

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]
    id: int
    name: str
    parent_module_id: int = Field(alias="parent_module")
    parent_subject_id: int = Field(alias="parent_subject")
    parent_module_name: str
    parent_subject_symbol: str
    parent_subject_color: str
    download: bool
    preview: ExercisePreviewTypes
    parent_subject_name: str
    parent_module_order: str
    order: str
    tags: list[str]
    patbas: PatbasEnum
    sync_status: SyncStatusEnum
    segel_path: str

    sync_message: str | None = Field(default=None)
    patbas_preview: ExercisePreviewTypes | None = Field(default=None)
    patbas_download: bool | None = Field(default=None)
    is_lecture: bool | None = Field(default=None)
    style: str | None = Field(default=None)
    on_creation_data: Any | None = Field(default=None)
    autocheck_tag: str | None = Field(default=None)
    autodone: bool | None = Field(default=None)
    expected_duration: str | None = Field(default=None)
    segel_brief: str | None = Field(default=None)

    _parent_module: "Module | None" = PrivateAttr(default=None)
    _parent_subject: "Subject | None" = PrivateAttr(default=None)

    @property
    def parent_module(self) -> "Module":
        """
        Lazily load the module this exercise belongs to.

        Returns:
            Module: The associated module instance.
        """
        if self._parent_module is None:
            self._parent_module = self.hive_client.get_module(self.parent_module_id)
        return self._parent_module

    @property
    def parent_subject(self) -> "Subject":
        """
        Lazily load the subject this exercise belongs to.

        Returns:
            Subject: The associated subject instance.
        """
        if self._parent_subject is None:
            self._parent_subject = self.hive_client.get_subject(self.parent_subject_id)
        return self._parent_subject

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        """
        Deserializes Exercise from dictionary payload.

        Args:
            src_dict (dict[str, Any]): The raw dictionary from the API response.
            hive_client (HiveClient): The client instance for deferred network operations.

        Returns:
            Self: An instantiated and validated Exercise model.
        """
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
        """
        Fetch all assignments associated with this exercise.

        Returns:
            Iterable[Assignment]: An iterable collection of assignment models.
        """
        return self.hive_client.get_assignments(
            exercise__id=self.id,
            exercise__parent_module__id=self.parent_module_id,
            exercise__parent_module__parent_subject__id=self.parent_subject_id,
        )

    def iter_assignments(self) -> Generator["Assignment", None, None]:
        """
        Allow iteration over this Exercise to yield its assignments.

        Yields:
            Generator[Assignment, None, None]: A generator producing Assignment instances.
        """
        yield from self.get_assignments()

    def delete(self) -> None:
        """
        Deletes the exercise using the underlying HiveClient.

        Returns:
            None
        """
        self.hive_client.delete_exercise(self)


ExerciseLike = TypeVar("ExerciseLike", Exercise, int)
