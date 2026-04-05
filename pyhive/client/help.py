"""Help requests mixin for HiveClient.

Provides listing and retrieval of Help request records via the Hive API.
"""

from typing import TYPE_CHECKING, Iterable, Optional

import httpx

from ..src.types.enums.help_type_enum import HelpTypeEnum
from ..src.types.enums.visibility_enum import VisibilityEnum
from ..src.types.exercise import ExerciseLike
from ..src.types.help_ import Help
from ..src.types.help_response import HelpResponse
from ..src.types.user import UserLike
from .client_shared import ClientCoreMixin
from .utils import resolve_item_or_id

if TYPE_CHECKING:
    from ..src.types.help_ import HelpLike


class HelpClientMixin(ClientCoreMixin):
    """
    Mixin class providing help-request API methods for HiveClient.

    Methods
    -------
    get_help_requests(...filters)
        List all or filtered help requests via the Hive API.
    get_help_request(help_id)
        Retrieve a single help request by id.
    get_help_responses(help)
        List help responses for a given help request.
    get_help_response(help, response_id)
        Retrieve a single help response by id for a given help request.
    get_help_response_student_files(help, response_id)
        Retrieve files attached to a specific help response (raw JSON).
    """

    def get_help_requests(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        *,
        created_by: Optional[int] = None,
        current: Optional[bool] = None,
        for_exercise__id: Optional[int] = None,
        for_exercise__parent_module__id: Optional[int] = None,
        for_exercise__parent_module__parent_subject__id: Optional[int] = None,
        free_text: Optional[str] = None,
        help_status__in: Optional[list[str]] = None,
        help_type__in: Optional[list[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        ordering: Optional[str] = None,
        user__classes__id: Optional[int] = None,
        user__classes__id__in: Optional[list[int]] = None,
        user__id__in: Optional[list[int]] = None,
        user__mentor__id: Optional[int] = None,
        user__mentor__id__in: Optional[list[int]] = None,
        user__program__id__in: Optional[list[int]] = None,
    ) -> Iterable[Help]:
        """Yield ``Help`` requests filtered by the provided criteria."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        return self._get_core_items(
            "/api/core/help/",
            Help,
            created_by=created_by,
            current=current,
            for_exercise__id=for_exercise__id,
            for_exercise__parent_module__id=for_exercise__parent_module__id,
            for_exercise__parent_module__parent_subject__id=for_exercise__parent_module__parent_subject__id,
            free_text=free_text,
            help_status__in=help_status__in,
            help_type__in=help_type__in,
            limit=limit,
            offset=offset,
            ordering=ordering,
            user__classes__id=user__classes__id,
            user__classes__id__in=user__classes__id__in,
            user__id__in=user__id__in,
            user__mentor__id=user__mentor__id,
            user__mentor__id__in=user__mentor__id__in,
            user__program__id__in=user__program__id__in,
        )

    def get_help_request(self, help_id: int) -> Help:
        """Return a single ``Help`` request by its id."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        data = self.get(f"/api/core/help/{help_id}/")
        assert isinstance(data, dict)
        return Help.from_dict(
            data,
            hive_client=self,
        )

    def get_help_responses(self, help_id: "HelpLike") -> Iterable[HelpResponse]:
        """Yield help responses for the given help request (by id or Help)."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        parent_id = resolve_item_or_id(help_id)
        return self._get_core_items(
            f"/api/core/help/{parent_id}/responses/",
            HelpResponse,
        )

    def get_help_response(self, help_id: "HelpLike", response_id: int) -> HelpResponse:
        """Return a single help response by id for the given help request."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        parent_id = resolve_item_or_id(help_id)
        data = self.get(
            f"/api/core/help/{parent_id}/responses/{response_id}/",
        )
        assert isinstance(data, dict)
        return HelpResponse.from_dict(
            data,
            hive_client=self,
        )

    def get_help_response_student_file(
        self, help_id: "HelpLike", response_id: int
    ) -> bytes | None:
        """Return the file attached to a specific help response"""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        parent_id = resolve_item_or_id(help_id)
        response = self._session.get(
            f"/api/core/help/{parent_id}/responses/{response_id}/student_files/"
        )
        if response.status_code == httpx.codes.NOT_FOUND.value:
            return None
        response.raise_for_status()
        return response.content

    def create_help_request(
        self,
        user: "UserLike",
        title: str,
        type_: HelpTypeEnum,
        exercise: "ExerciseLike",
        visibility: VisibilityEnum,
    ) -> Help:
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        return Help.from_dict(
            self.post(
                "/api/core/help/",
                {
                    "user": resolve_item_or_id(user),
                    "title": title,
                    "help_type": type_.value,
                    "exercise_id": resolve_item_or_id(exercise),
                    "visibility": visibility.value,
                },
            ),
            hive_client=self,
        )

    def create_chat(
        self,
        *,
        with_user: "UserLike",
        title: str,
        about_exercise: Optional["ExerciseLike"] = None,
        visibility: VisibilityEnum = VisibilityEnum.AUTHOR_ONLY,
    ) -> Help:
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        return Help.from_dict(
            self.post(
                "/api/core/help/",
                {
                    "user": resolve_item_or_id(with_user),
                    "title": title,
                    "help_type": HelpTypeEnum.CHAT,
                    "exercise_id": resolve_item_or_id(about_exercise),
                    "visibility": visibility.value,
                },
            ),
            hive_client=self,
        )

    def delete_help_request(self, help_request: "HelpLike") -> None:
        self.delete(f"/api/core/help/{resolve_item_or_id(help_request)}/")

    def delete_chat(self, chat: "HelpLike") -> None:
        self.delete_help_request(help_request=chat)
