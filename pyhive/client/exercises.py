"""
Exercise resource mixin for HiveClient.

Provides listing and retrieval of Exercise records, with rich filtering, via the Hive API.
Intended for mixing into the main HiveClient only.
"""

from typing import TYPE_CHECKING, Iterable, Optional

from ..src.types.enums.exercise_patbas_enum import PatbasEnum
from ..src.types.enums.exercise_preview_types import ExercisePreviewTypes
from ..src.types.exercise import Exercise
from .client_shared import ClientCoreMixin
from .utils import resolve_item_or_id

if TYPE_CHECKING:
    from ..src.types.exercise import ExerciseLike
    from ..src.types.module import ModuleLike
    from ..src.types.subject import SubjectLike


class ExerciseClientMixin(ClientCoreMixin):
    """
    Mixin class providing exercise-related API methods for HiveClient.

    Methods
    -------
    get_exercises(parent_module__id=None, parent_module=None, parent_subject=None, exercise_name=None, ...)
        List all or filtered exercises via the Hive API. Supports advanced hierarchical filtering.
    get_exercise(exercise_id)
        Retrieve a single exercise by id.
    """

    # NOTE: Intended to be used only as part of the HiveClient composite class
    def get_exercises(  # pylint: disable=too-many-arguments
        self,
        *,
        parent_module__id: Optional[int] = None,
        parent_module__parent_subject__id: Optional[int] = None,
        parent_module__parent_subject__parent_program__id__in: Optional[
            list[int]
        ] = None,
        queue__id: Optional[int] = None,
        tags__id__in: Optional[list[int]] = None,
        parent_module: Optional["ModuleLike"] = None,
        parent_subject: Optional["SubjectLike"] = None,
        exercise_name: Optional[str] = None,
    ) -> Iterable[Exercise]:
        """Yield ``Exercise`` objects, supporting rich parent-based filtering."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        if parent_module is not None and parent_module__id is not None:
            assert parent_module__id == resolve_item_or_id(parent_module)
        parent_module__id = (
            parent_module__id
            if parent_module__id is not None
            else resolve_item_or_id(parent_module)
        )
        if parent_subject is not None and parent_module__parent_subject__id is not None:
            assert parent_module__parent_subject__id == resolve_item_or_id(
                parent_subject
            )
        parent_module__parent_subject__id = (
            parent_module__parent_subject__id
            if parent_module__parent_subject__id is not None
            else resolve_item_or_id(parent_subject)
        )
        exercises: Iterable[Exercise] = self._get_core_items(
            "/api/core/course/exercises/",
            Exercise,
            parent_module__id=parent_module__id,
            parent_module__parent_subject__id=parent_module__parent_subject__id,
            parent_module__parent_subject__parent_program__id__in=parent_module__parent_subject__parent_program__id__in,
            queue__id=queue__id,
            tags__id__in=tags__id__in,
        )
        if exercise_name is not None:
            exercises = filter(lambda e: e.name == exercise_name, exercises)
        return exercises

    def get_exercise(self, exercise_id: int) -> Exercise:
        """Return a single ``Exercise`` by its id."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        data = self.get(f"/api/core/course/exercises/{exercise_id}/")
        assert isinstance(data, dict)
        return Exercise.from_dict(
            data,
            hive_client=self,
        )

    def create_exercise(
        self,
        name: str,
        order: int,
        parent_module: "ModuleLike",
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
        tags: Optional[list[str]] = None,
    ) -> Exercise:
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"

        payload: dict[str, str | int | list[int] | list[str]] = {
            "name": name,
            "parent_module": resolve_item_or_id(parent_module),
            "download": download,
            "preview": preview,
            "patbas_preview": patbas_preview,
            "patbas_download": patbas_download,
            "is_lecture": is_lecture,
            "style": style,
            "order": order,
            "tags": tags if tags is not None else [],
            "patbas": patbas,
            "on_creation_data": on_creation_data,
            "autocheck_tag": autocheck_tag,
            "autodone": autodone,
            "expected_duration": expected_duration,
            "segel_brief": segel_brief,
        }

        return Exercise.from_dict(
            self.post("/api/core/course/exercises/", payload),
            hive_client=self,
        )

    def delete_exercise(self, exercise: "ExerciseLike") -> None:
        self.delete(f"/api/core/course/exercises/{resolve_item_or_id(exercise)}/")
