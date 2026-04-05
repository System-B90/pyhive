"""
Name: module.py
Purpose: Module model definition for the Hive system.
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
from .exercise import Exercise

if TYPE_CHECKING:
    from ...client import HiveClient
    from .subject import Subject


class Module(HiveCoreItem):
    """
    Course Subject Module.

    Attributes:
        id: Unique identifier.
        name: Name of the module.
        parent_subject_id: ID of the parent subject.
        order: Order of display within the subject.
        sync_status: Synchronization status.
        sync_message: Optional error or status message.
        parent_program_name: Name of the program the subject belongs to.
        parent_subject_name: Name of the parent subject.
        parent_subject_symbol: Symbol of the parent subject.
        segel_path: Network path accessible to staff.
    """

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]
    id: int
    name: str
    parent_subject_id: int = Field(alias="parent_subject")
    order: str
    sync_status: SyncStatusEnum
    sync_message: str | None = Field(default=None)
    parent_program_name: str
    parent_subject_name: str
    parent_subject_symbol: str
    segel_path: str

    _parent_subject: "Subject | None" = PrivateAttr(default=None)

    @property
    def parent_subject(self) -> "Subject":
        """
        Lazily loads and returns the parent subject.

        Returns:
            Subject: The associated parent subject entity.
        """
        if self._parent_subject is None:
            self._parent_subject = self.hive_client.get_subject(self.parent_subject_id)
        return self._parent_subject

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        """
        Deserializes a Module instance from a dictionary payload.

        Args:
            src_dict (dict[str, Any]): The raw dictionary from the API response.
            hive_client (HiveClient): The client instance for deferred network operations.

        Returns:
            Self: An instantiated and validated Module model.
        """
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Module):
            return False
        return self.id == value.id and self.parent_subject_id == value.parent_subject_id

    def __lt__(self, value: object) -> bool:
        if not isinstance(value, Module):
            return NotImplemented
        return self.order < value.order

    def __hash__(self) -> int:
        return hash((self.id, self.parent_subject_id))

    def get_exercises(self) -> Iterable[Exercise]:
        """
        Fetches all exercises within this module.

        Returns:
            Iterable[Exercise]: An iterable collection of exercise models.
        """
        return self.hive_client.get_exercises(parent_module__id=self.id)

    def get_exercise(self, exercise_name: str) -> Exercise:
        """
        Fetches a specific exercise by name within this module.

        Args:
            exercise_name (str): The name of the exercise to retrieve.

        Returns:
            Exercise: The matched exercise model.

        Raises:
            ValueError: If no exercise or multiple exercises are found.
        """
        exercises = list(
            self.hive_client.get_exercises(
                parent_module__id=self.id,
                exercise_name=exercise_name,
            )
        )

        if len(exercises) == 0:
            raise ValueError(
                f"Exercise '{exercise_name}' not found in module '{self.name}'"
            )
        if len(exercises) > 1:
            raise ValueError(
                f"Multiple exercises named '{exercise_name}' found in module '{self.name}'"
            )
        return exercises[0]

    def iter_exercises(self) -> Generator["Exercise", None, None]:
        """
        Allows iteration over this Module to yield its exercises.

        Yields:
            Generator[Exercise, None, None]: A generator producing Exercise instances.
        """
        yield from self.get_exercises()

    def delete(self) -> None:
        """
        Deletes the module using the underlying HiveClient.

        Returns:
            None
        """
        self.hive_client.delete_module(self)

    def create_exercise(
        self,
        name: str,
        order: int,
        *,
        download: bool = False,
        preview: ExercisePreviewTypes = ExercisePreviewTypes.DISABLED,
        patbas_preview: ExercisePreviewTypes = ExercisePreviewTypes.DISABLED,
        style: str = "",
        patbas_download: bool = False,
        patbas: PatbasEnum = PatbasEnum.NEVER,
        on_creation_data: str = "",
        autocheck_tag: str = "",
        autodone: bool = False,
        expected_duration: str = "",
        segel_brief: str = "",
        is_lecture: bool = False,
        tags: list[str] | None = None,
    ) -> Exercise:
        """
        Creates a new exercise in this module.

        Args:
            name (str): The exercise name.
            order (int): The display order.
            download (bool, optional): Enable downloads. Defaults to False.
            preview (ExercisePreviewTypes, optional): Preview type. Defaults to DISABLED.
            patbas_preview (ExercisePreviewTypes, optional): Patbas preview. Defaults to DISABLED.
            style (str, optional): CSS style string. Defaults to "".
            patbas_download (bool, optional): Enable patbas download. Defaults to False.
            patbas (PatbasEnum, optional): Patbas enum state. Defaults to NEVER.
            on_creation_data (str, optional): Creation hook data. Defaults to "".
            autocheck_tag (str, optional): Tag for autochecking. Defaults to "".
            autodone (bool, optional): Auto-mark as done. Defaults to False.
            expected_duration (str, optional): Time estimate. Defaults to "".
            segel_brief (str, optional): Staff briefing context. Defaults to "".
            is_lecture (bool, optional): Flag if lecture. Defaults to False.
            tags (list[str] | None, optional): Associated tags. Defaults to None.

        Returns:
            Exercise: The newly created exercise model.
        """
        return self.hive_client.create_exercise(
            name=name,
            order=order,
            parent_module=self,
            download=download,
            preview=preview,
            patbas_preview=patbas_preview,
            style=style,
            patbas_download=patbas_download,
            patbas=patbas,
            on_creation_data=on_creation_data,
            autocheck_tag=autocheck_tag,
            autodone=autodone,
            expected_duration=expected_duration,
            segel_brief=segel_brief,
            is_lecture=is_lecture,
            tags=tags,
        )


ModuleLike = TypeVar("ModuleLike", Module, int)
