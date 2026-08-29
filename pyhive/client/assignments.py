"""
Assignment resource mixin for HiveClient.

Adds methods for listing and retrieving Assignment records via the Hive API. Meant only
for use as a mixin on HiveClient.
"""

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Optional

from ..src.types.assignment import Assignment
from ..src.types.assignment_notification import AssignmentNotification
from .client_shared import ClientCoreMixin
from .utils import assert_mutually_exclusive_filters, resolve_item_or_id

if TYPE_CHECKING:
    from ..src.types.assignment import AssignmentLike
    from ..src.types.module import ModuleLike
    from ..src.types.subject import SubjectLike
    from ..src.types.user import UserLike


class AssignmentClientMixin(ClientCoreMixin):
    """
    Mixin class providing assignment-related API methods to HiveClient.

    Methods
    -------
    get_assignments(...various filters...)
        List all or filtered assignments, supporting complex relational filters.
    get_assignment(assignment_id)
        Retrieve a single assignment by its id.
    """

    def get_assignments(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        *,
        exercise__id: int | None = None,
        exercise__parent_module__id: int | None = None,
        exercise__parent_module__parent_subject__id: int | None = None,
        exercise__tags__id__in: Sequence[int] | None = None,
        queue__id: int | None = None,
        user__classes__id: int | None = None,
        user__classes__id__in: Sequence[int] | None = None,
        user__id__in: Sequence[int] | None = None,
        user__mentor__id: int | None = None,
        user__mentor__id__in: Sequence[int] | None = None,
        user__program__id__in: Sequence[int] | None = None,
        # Non built-in filters
        parent_module: Optional["ModuleLike"] = None,
        parent_subject: Optional["SubjectLike"] = None,
        for_user: Optional["UserLike"] = None,
        for_mentees_of: Optional["UserLike"] = None,
    ) -> Iterable[Assignment]:
        """Yield ``Assignment`` objects filtered by the provided criteria."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"

        if parent_module is not None and exercise__parent_module__id is not None:
            assert exercise__parent_module__id == resolve_item_or_id(parent_module)
        exercise__parent_module__id = (
            exercise__parent_module__id
            if exercise__parent_module__id is not None
            else resolve_item_or_id(parent_module)
        )
        if (
            parent_subject is not None
            and exercise__parent_module__parent_subject__id is not None
        ):
            assert exercise__parent_module__parent_subject__id == resolve_item_or_id(
                parent_subject
            )
        exercise__parent_module__parent_subject__id = (
            exercise__parent_module__parent_subject__id
            if exercise__parent_module__parent_subject__id is not None
            else resolve_item_or_id(parent_subject)
        )

        assert_mutually_exclusive_filters(user__classes__id, user__classes__id__in)

        assert (not (user__id__in is not None and for_user is not None)) or (
            len(user__id__in) == 1 and user__id__in[0] == resolve_item_or_id(for_user)
        ), "Filters user__id__in and for_user conflict!"
        if for_user is not None:
            user__id__in = [resolve_item_or_id(for_user)]

        assert_mutually_exclusive_filters(
            user__mentor__id, user__mentor__id__in, for_mentees_of
        )
        if for_mentees_of is not None:
            user__mentor__id = resolve_item_or_id(for_mentees_of)

        return self._get_core_items(
            "/api/core/assignments/",
            Assignment,
            exercise__id=exercise__id,
            exercise__parent_module__id=exercise__parent_module__id,
            exercise__parent_module__parent_subject__id=exercise__parent_module__parent_subject__id,
            exercise__tags__id__in=exercise__tags__id__in,
            queue__id=queue__id,
            user__classes__id=user__classes__id,
            user__classes__id__in=user__classes__id__in,
            user__id__in=user__id__in,
            user__mentor__id=user__mentor__id,
            user__mentor__id__in=user__mentor__id__in,
            user__program__id__in=user__program__id__in,
        )

    def get_assignment(self, assignment_id: int) -> Assignment:
        """Return a single ``Assignment`` by its id."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        data = self.get(f"/api/core/assignments/{assignment_id}/")
        assert isinstance(data, dict)
        return Assignment.from_dict(
            data,
            hive_client=self,
        )

    def update_assignment(self, assignment: Assignment) -> Assignment:
        """Commits the local state of the assignment to the server."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        response = self.put(
            f"/api/core/assignments/{assignment.id}/",
            assignment.to_dict(),
        )
        return Assignment.from_dict(response, hive_client=self)

    def patch_assignment(
        self, assignment: "AssignmentLike", **fields: object
    ) -> Assignment:
        """Partially update an assignment with the given fields."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        assignment_id = resolve_item_or_id(assignment)
        response = self.patch(f"/api/core/assignments/{assignment_id}/", dict(fields))
        return Assignment.from_dict(response, hive_client=self)

    def delete_assignment(self, assignment: "AssignmentLike") -> None:
        """Delete an assignment by id or instance."""
        self.delete(f"/api/core/assignments/{resolve_item_or_id(assignment)}/")

    def lock_assignment(self, assignment: "AssignmentLike") -> None:
        """Lock ``assignment`` so the student cannot submit to it."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        self.put_empty(f"/api/core/assignments/{resolve_item_or_id(assignment)}/lock/")

    def unlock_assignment(self, assignment: "AssignmentLike") -> None:
        """Unlock a previously locked ``assignment``."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        self.put_empty(
            f"/api/core/assignments/{resolve_item_or_id(assignment)}/unlock/"
        )

    def subscribe_to_assignment(self, assignment: "AssignmentLike") -> None:
        """Subscribe the current user to notifications about ``assignment``."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        self.put_empty(
            f"/api/core/assignments/{resolve_item_or_id(assignment)}/subscribe/"
        )

    def unsubscribe_from_assignment(self, assignment: "AssignmentLike") -> None:
        """Unsubscribe the current user from notifications about ``assignment``."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        self.put_empty(
            f"/api/core/assignments/{resolve_item_or_id(assignment)}/unsubscribe/"
        )

    # --- Latest-activity notifications ---

    def get_latest_assignments(  # pylint: disable=too-many-arguments
        self,
        *,
        last_staff_updated__gt: str | None = None,
        user__classes__id: int | None = None,
        user__id__in: list[int] | None = None,
        user__mentor__id: int | None = None,
    ) -> Iterable[AssignmentNotification]:
        """Yield up-to-100 latest submitted assignments for staff notification feeds."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        return self._get_core_items(
            "/api/core/assignments/latest/",
            AssignmentNotification,
            last_staff_updated__gt=last_staff_updated__gt,
            user__classes__id=user__classes__id,
            user__id__in=user__id__in,
            user__mentor__id=user__mentor__id,
        )

    def create_latest_assignment(self, **fields: object) -> AssignmentNotification:
        """Create an assignment latest-activity record (staff only)."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        return AssignmentNotification.from_dict(
            self.post("/api/core/assignments/latest/", dict(fields)), hive_client=self
        )

    def update_latest_assignment(
        self, latest_id: int, **fields: object
    ) -> AssignmentNotification:
        """Partially update an assignment latest-activity record."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        return AssignmentNotification.from_dict(
            self.patch(f"/api/core/assignments/latest/{latest_id}/", dict(fields)),
            hive_client=self,
        )

    def delete_latest_assignment(self, latest_id: int) -> None:
        """Delete an assignment latest-activity record by id."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        self.delete(f"/api/core/assignments/latest/{latest_id}/")
