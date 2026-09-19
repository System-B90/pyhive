"""Lessons mixin for HiveClient.

Covers lessons and their nested queue rules under ``/api/core/schedule/lessons/``.
Meant only for use as a mixin on HiveClient.
"""

from collections.abc import Iterable
from typing import TYPE_CHECKING

from ..src.types.lesson import Lesson
from ..src.types.lesson_rule import LessonRule
from .client_shared import ClientCoreMixin
from .utils import UUIDLike, resolve_item_or_id, resolve_item_or_uuid

if TYPE_CHECKING:
    from ..src.types.module import ModuleLike


class LessonClientMixin(ClientCoreMixin):
    """Mixin that exposes lesson endpoints."""

    def get_lessons(
        self,
        *,
        module__id: int | None = None,
        module: "ModuleLike | None" = None,
    ) -> Iterable[Lesson]:
        """Yield ``Lesson`` objects, optionally filtered by module."""
        if module is not None:
            resolved_module_id = resolve_item_or_id(module)
            assert module__id is None or module__id == resolved_module_id
            module__id = resolved_module_id
        return self._get_core_items(
            "/api/core/schedule/lessons/",
            Lesson,
            module__id=module__id,
        )

    def get_lesson(self, lesson_id: "UUIDLike | Lesson") -> Lesson:
        """Return a single ``Lesson`` by its id."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        data = self.get(
            f"/api/core/schedule/lessons/{resolve_item_or_uuid(lesson_id)}/"
        )
        assert isinstance(data, dict)
        return Lesson.from_dict(data, hive_client=self)

    def create_lesson(
        self,
        name: str,
        module: "ModuleLike",
        *,
        description: str = "",
    ) -> Lesson:
        """Create a lesson attached to a module."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        payload: dict[str, object] = {
            "name": name,
            "module_id": resolve_item_or_id(module),
            "description": description,
        }
        return Lesson.from_dict(
            self.post("/api/core/schedule/lessons/", payload), hive_client=self
        )

    def update_lesson(self, lesson: "UUIDLike | Lesson", **fields: object) -> Lesson:
        """Partially update a lesson with the given fields (name/description)."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        lesson_id = resolve_item_or_uuid(lesson)
        data = self.patch(f"/api/core/schedule/lessons/{lesson_id}/", dict(fields))
        assert isinstance(data, dict)
        return Lesson.from_dict(data, hive_client=self)

    def delete_lesson(self, lesson_id: "UUIDLike | Lesson") -> None:
        """Delete a lesson by id."""
        self.delete(f"/api/core/schedule/lessons/{resolve_item_or_uuid(lesson_id)}/")

    # --- Rules ---

    def get_lesson_rules(self, *, lesson: "UUIDLike | Lesson") -> Iterable[LessonRule]:
        """Yield the queue rules configured for ``lesson`` (id or instance)."""
        lesson_id = resolve_item_or_uuid(lesson)
        return self._get_core_items(
            f"/api/core/schedule/lessons/{lesson_id}/rules/",
            LessonRule,
        )

    def create_lesson_rule(
        self,
        *,
        lesson: "UUIDLike | Lesson",
        parent_rule: UUIDLike | None = None,
        student_groups: list[int] | None = None,
        queue: int | None = None,
    ) -> LessonRule:
        """Create a queue rule for ``lesson``."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        lesson_id = resolve_item_or_uuid(lesson)
        parent_rule_id = resolve_item_or_uuid(parent_rule)
        payload: dict[str, object] = {
            "parent_rule": str(parent_rule_id) if parent_rule_id is not None else None,
            "student_groups": student_groups if student_groups is not None else [],
            "queue": queue,
        }
        data = self.post(f"/api/core/schedule/lessons/{lesson_id}/rules/", payload)
        assert isinstance(data, dict)
        return LessonRule.from_dict(data, hive_client=self)

    def update_lesson_rule(
        self,
        *,
        lesson: "UUIDLike | Lesson",
        rule_id: "UUIDLike | LessonRule",
        **fields: object,
    ) -> LessonRule:
        """Partially update a lesson rule with the given fields."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        lesson_id = resolve_item_or_uuid(lesson)
        data = self.patch(
            f"/api/core/schedule/lessons/{lesson_id}/rules/{resolve_item_or_uuid(rule_id)}/",
            dict(fields),
        )
        assert isinstance(data, dict)
        return LessonRule.from_dict(data, hive_client=self)

    def delete_lesson_rule(
        self, *, lesson: "UUIDLike | Lesson", rule_id: "UUIDLike | LessonRule"
    ) -> None:
        """Delete a lesson rule by id."""
        lesson_id = resolve_item_or_uuid(lesson)
        self.delete(
            f"/api/core/schedule/lessons/{lesson_id}/rules/{resolve_item_or_uuid(rule_id)}/"
        )
