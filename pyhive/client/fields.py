"""Exercise form fields mixin for HiveClient.

Provides methods to list and retrieve form fields for a specific exercise.
"""

from typing import TYPE_CHECKING, Any, Iterable, cast

from ..src.types.form_field import FormField
from .client_shared import ClientCoreMixin
from .utils import resolve_item_or_id

if TYPE_CHECKING:
    from ..src.types.exercise import ExerciseLike


class FieldsClientMixin(ClientCoreMixin):
    """Mixin that exposes form-field endpoints for exercises."""

    def get_exercise_fields(
        self,
        exercise: "ExerciseLike",
    ) -> Iterable[FormField]:
        """Yield all form fields for the given ``exercise`` (id or instance)."""
        exercise_id = resolve_item_or_id(exercise)
        return self._get_core_items(
            f"/api/core/course/exercises/{exercise_id}/fields/",
            FormField,
            exercise_id=exercise_id,
        )

    def get_exercise_field(
        self,
        exercise: "ExerciseLike",
        field_id: int,
    ) -> FormField:
        """Return a single form field for ``exercise`` by ``field_id``."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        exercise_id = resolve_item_or_id(exercise)
        return FormField.from_dict(
            cast(
                dict[str, Any],
                self.get(
                    f"/api/core/course/exercises/{exercise_id}/fields/{field_id}/"
                ),
            ),
            hive_client=self,
        )
