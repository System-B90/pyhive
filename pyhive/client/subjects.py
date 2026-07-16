"""
Subject resource mixin for HiveClient.

Provides methods for listing and retrieving Subject records via the Hive API.
Intended for use as a mixin on the main HiveClient only.
"""

from typing import TYPE_CHECKING, Iterable, Optional

from ..src.types.subject import Subject, SubjectLike
from .client_shared import ClientCoreMixin
from .utils import resolve_item_or_id

if TYPE_CHECKING:
    from ..src.types.program import ProgramLike


class SubjectClientMixin(ClientCoreMixin):
    """
    Mixin class adding subject-related API methods to the HiveClient.

    Methods
    -------
    get_subjects(parent_program__id__in=None, parent_program=None, subject_name=None)
        List all or filtered subjects via the Hive API. Supports filtering by program.
    get_subject(subject_id)
        Retrieve a single subject record by its id.
    """

    def get_subjects(
        self,
        parent_program__id__in: Optional[list[int]] = None,
        # Non built-in filters
        parent_program: Optional["ProgramLike"] = None,
        subject_name: Optional[str] = None,
    ) -> Iterable[Subject]:
        """Yield ``Subject`` objects, supporting program-based filtering."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        assert (
            not (parent_program__id__in is not None and parent_program is not None)
        ) or (
            len(parent_program__id__in) == 1
            and parent_program__id__in[0] == resolve_item_or_id(parent_program)
        ), "Mismatch between parent_program__id__in and parent_program filters!"
        if parent_program is not None:
            parent_program__id__in = [resolve_item_or_id(parent_program)]

        subjects: Iterable[Subject] = self._get_core_items(
            "/api/core/course/subjects/",
            Subject,
            parent_program__id__in=parent_program__id__in,
        )
        if subject_name is not None:
            subjects = filter(lambda s: s.name == subject_name, subjects)
        return subjects

    def get_subject(self, subject_id: int) -> Subject:
        """Return a single ``Subject`` by its id."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        data = self.get(f"/api/core/course/subjects/{subject_id}/")
        assert isinstance(data, dict)
        return Subject.from_dict(
            data,
            hive_client=self,
        )

    def create_subject(
        self,
        symbol: str,
        name: str,
        program: "ProgramLike",
        color: str,
        segel_brief: str = "",
    ) -> Subject:
        """
        Create a Subject via the Hive API.
        """

        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"

        assert program is not None, "Subject creation requires a valid program!"

        payload: dict[str, object] = {
            "name": name,
            "symbol": symbol,
            "parent_program": resolve_item_or_id(program),
            "color": color,
            "segel_brief": segel_brief,
        }

        response = self.post("/api/core/course/subjects/", payload)

        return Subject.from_dict(response, hive_client=self)

    def delete_subject(self, subject: "SubjectLike") -> None:
        assert subject is not None, "Cannot delete None subject!"
        self.delete(f"/api/core/course/subjects/{resolve_item_or_id(subject)}/")
