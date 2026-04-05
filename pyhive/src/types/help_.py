"""Model for student help requests (auto-generated).

This module defines the :class:`Help` model used to represent student
help requests and provides serialization helpers.
"""

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self, TypeVar, Union, cast

from attr import field
from attrs import define

from .common import UNSET, Unset
from .core_item import HiveCoreItem
from .enums.help_status_enum import HelpStatusEnum
from .enums.help_type_enum import HelpTypeEnum
from .enums.visibility_enum import VisibilityEnum

if TYPE_CHECKING:
    from ...client import HiveClient
    from .exercise import Exercise
    from .help_response_segel_nested import HelpResponseSegelNested
    from .notification_nested import NotificationNested
    from .user import User


T = TypeVar("T", bound="Help")


@define
class Help(HiveCoreItem):
    """A student's help request.

    Attributes:
    id (int):
    user (int):
    checker (Union[None, int]):
    checker_first_name (str):
    checker_last_name (str):
    is_subscribed (bool):
    help_type (HelpTypeEnum):
        * `Exercise` - Exercise
        * `Medical` - Medical
        * `Error` - Error
        * `Music` - Music
        * `Request` - Request
        * `Other` - Other
        * `Chat` - Chat
    help_status (HelpStatusEnum):
        * `Resolved` - Resolved
        * `Open` - Open
    for_exercise (Union['Exercise', None]):
    responses (list['HelpResponseSegelNested']):
    notifications (list['NotificationNested']):
    title (Union[Unset, str]):
    visibility (Union[Unset, VisibilityEnum]):
        * `All Staff` - Allstaff
        * `All Staff And Checkers` - Allstaffandcheckers
        * `Author Only` - Authoronly

    """

    hive_client: "HiveClient"
    id: int
    user_id: int
    _user: Union["User", None] = field(init=False, default=None)
    checker_id: None | int
    _checker: Union["User", None] = field(init=False, default=None)
    checker_first_name: str
    checker_last_name: str
    is_subscribed: bool
    help_type: HelpTypeEnum
    help_status: HelpStatusEnum
    for_exercise_id: int | None
    _for_exercise: Union["Exercise", None] = field(init=False, default=None)
    responses: list["HelpResponseSegelNested"]
    notifications: list["NotificationNested"]
    title: Unset | str = UNSET
    visibility: Unset | VisibilityEnum = UNSET

    def to_dict(self) -> dict[str, Any]:  # pylint: disable=too-many-locals
        """Serialize this Help instance to a plain dictionary.

        Returns:
            A JSON-serializable mapping representing this help request.
        """

        # Import locally to avoid circular imports at module import time.
        # Keep the import local but silence pylint's import-outside-toplevel.
        from .exercise import Exercise  # pylint: disable=import-outside-toplevel

        # Keep the attribute name `id` as generated; silence redefined-builtin warning.
        id = self.id  # pylint: disable=redefined-builtin

        user = self.user

        checker_id = self.checker_id

        checker_first_name = self.checker_first_name

        checker_last_name = self.checker_last_name

        is_subscribed = self.is_subscribed

        help_type = self.help_type.value

        help_status = self.help_status.value

        for_exercise: None | dict[str, Any]
        for_exercise = (
            self.for_exercise.to_dict()
            if isinstance(self.for_exercise, Exercise)
            else self.for_exercise
        )

        responses: list[dict[str, Any]] = []
        for responses_item_data in self.responses:
            responses_item = responses_item_data.to_dict()
            responses.append(responses_item)

        notifications: list[dict[str, Any]] = []
        for notifications_item_data in self.notifications:
            notifications_item = notifications_item_data.to_dict()
            notifications.append(notifications_item)

        title = self.title

        visibility: Unset | str = UNSET
        if not isinstance(self.visibility, Unset):
            visibility = self.visibility.value

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "id": id,
                "user": user,
                "checker": checker_id,
                "checker_first_name": checker_first_name,
                "checker_last_name": checker_last_name,
                "is_subscribed": is_subscribed,
                "help_type": help_type,
                "help_status": help_status,
                "for_exercise": for_exercise,
                "responses": responses,
                "notifications": notifications,
            },
        )
        if title is not UNSET:
            field_dict["title"] = title
        if visibility is not UNSET:
            field_dict["visibility"] = visibility

        return field_dict

    @classmethod
    def from_dict(  # pylint: disable=too-many-locals
        cls, src_dict: Mapping[str, Any], hive_client: "HiveClient"
    ) -> Self:
        """Deserialize a Help instance from a mapping.

        Args:
            src_dict: The source mapping (typically parsed JSON).
            hive_client: The HiveClient used for lazy-loading related objects.

        Returns:
            A populated :class:`Help` instance.
        """

        # Local imports to avoid runtime import cycles; keep but silence pylint.
        from .help_response_segel_nested import HelpResponseSegelNested  # pylint: disable=import-outside-toplevel
        from .notification_nested import NotificationNested  # pylint: disable=import-outside-toplevel

        d = dict(src_dict)
        id = d.pop("id")

        user_id = d.pop("user")

        def _parse_checker(data: object) -> None | int:
            if data is None:
                return data
            return cast("None | int", data)

        checker_id = _parse_checker(d.pop("checker"))

        checker_first_name = d.pop("checker_first_name")

        checker_last_name = d.pop("checker_last_name")

        is_subscribed = d.pop("is_subscribed")

        help_type = HelpTypeEnum(d.pop("help_type"))

        help_status = HelpStatusEnum(d.pop("help_status"))

        def _parse_for_exercise(data: object) -> int | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError
                return cast("int", data["id"])
            except Exception:  # pylint: disable=broad-except
                # When the structure is unexpected, treat as missing.
                return None

        for_exercise_id = _parse_for_exercise(d.pop("for_exercise"))

        responses = [
            HelpResponseSegelNested.from_dict(
                cast(dict[str, Any], responses_item_data),
                hive_client=hive_client,
            )
            for responses_item_data in d.pop("responses")
        ]

        notifications: list[NotificationNested] = [
            NotificationNested.from_dict(
                cast(dict[str, Any], notifications_item_data),
                hive_client=hive_client,
            )
            for notifications_item_data in d.pop("notifications")
        ]

        title = d.pop("title", UNSET)

        _visibility = d.pop("visibility", UNSET)
        visibility: Unset | VisibilityEnum
        visibility = (
            UNSET if isinstance(_visibility, Unset) else VisibilityEnum(_visibility)
        )

        return cls(
            id=id,
            user_id=user_id,
            checker_id=checker_id,
            checker_first_name=checker_first_name,
            checker_last_name=checker_last_name,
            is_subscribed=is_subscribed,
            help_type=help_type,
            help_status=help_status,
            for_exercise_id=for_exercise_id,
            responses=responses,
            notifications=notifications,
            title=title,
            visibility=visibility,
            hive_client=hive_client,
        )

    @property
    def for_exercise(self) -> Union["Exercise", None]:
        """Lazily load and return the related Exercise, if any.

        Returns:
            The resolved :class:`Exercise` instance or None when not set.
        """
        if self.for_exercise_id is None:
            return None
        if self._for_exercise is None:
            self._for_exercise = self.hive_client.get_exercise(self.for_exercise_id)
        return self._for_exercise

    @property
    def user(self) -> "User":
        """User which opened this help request.

        Returns:
            User: The user instance.

        """
        if self._user is None:
            self._user = self.hive_client.get_user(self.user_id)
        return self._user

    def delete(self) -> None:
        self.hive_client.delete_help_request(self)


HelpLike = TypeVar("HelpLike", Help, int)
