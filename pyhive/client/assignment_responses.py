"""
Assignment Response resource mixin for HiveClient.

Provides methods for listing and retrieving AssignmentResponse records for a given assignment
through the Hive API. Intended only for use as a mixin on HiveClient.
"""

from typing import TYPE_CHECKING, Any, Iterable, cast

from ..src.types.assignment_response import AssignmentResponse
from .client_shared import ClientCoreMixin
from .utils import resolve_item_or_id

if TYPE_CHECKING:
    from ..src.types.assignment import AssignmentLike


class AssignmentResponsesClientMixin(ClientCoreMixin):
    """
    Mixin class providing assignment response API methods to HiveClient.

    Methods
    -------
    get_assignment_responses(assignment)
        List all assignment responses for a single assignment.
    get_assignment_response(assignment, response_id)
        Retrieve one assignment response by id for a given assignment.
    """

    def get_assignment_responses(
        self, assignment: "AssignmentLike"
    ) -> Iterable[AssignmentResponse]:
        """Yield assignment responses for the provided ``assignment`` (id or instance)."""
        assignment_id = resolve_item_or_id(assignment)
        return self._get_core_items(
            f"/api/core/assignments/{assignment_id}/responses/",
            AssignmentResponse,
            assignment_id=assignment_id,
        )

    def get_assignment_response(
        self, assignment: "AssignmentLike", response_id: int
    ) -> AssignmentResponse:
        """Return a single response by ``response_id`` for the given ``assignment``."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"

        assignment_id = resolve_item_or_id(assignment)
        return AssignmentResponse.from_dict(
            cast(
                dict[str, Any],
                self.get(
                    f"/api/core/assignments/{assignment_id}/responses/{response_id}/"
                ),
            ),
            assignment_id=assignment_id,
            hive_client=self,
        )
