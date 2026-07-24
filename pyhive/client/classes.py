"""
Class resource mixin for HiveClient.

Provides listing and retrieval of Class records from the Hive API. Use only as a mixin for the main HiveClient.
"""

from collections.abc import Iterable
from typing import TYPE_CHECKING

from ..src.types.class_ import Class
from ..src.types.enums.class_type_enum import ClassTypeEnum
from .client_shared import ClientCoreMixin
from .utils import resolve_item_or_id

if TYPE_CHECKING:
    from ..src.types.class_ import ClassLike
    from ..src.types.program import ProgramLike
    from ..src.types.user import UserLike


class ClassesClientMixin(ClientCoreMixin):
    """
    Mixin class providing class-related API methods for HiveClient.

    Methods
    -------
    get_classes(id__in=None, name=None, program__id__in=None, type_=None, ...)
        List all or filtered classes via the Hive API. Supports multiple relationship filters.
    get_class(class_id)
        Retrieve a single class by id.
    """

    def get_classes(
        self,
        *,
        id__in: list[int] | None = None,
        name: str | None = None,
        program__id__in: list[int] | None = None,
        type_: ClassTypeEnum | None = None,
    ) -> Iterable[Class]:
        """Yield ``Class`` objects filtered by the provided criteria."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        return self._get_core_items(
            "/api/core/management/classes/",
            Class,
            id__in=id__in,
            name=name,
            program__id__in=program__id__in,
            type=type_,
        )

    def get_class(
        self,
        class_id: int,
    ) -> Class:
        """Return a single ``Class`` by its id."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        data = self.get(f"/api/core/management/classes/{class_id}/")
        assert isinstance(data, dict)
        return Class.from_dict(
            data,
            hive_client=self,
        )

    def create_class(
        self,
        name: str,
        *,
        program: "ProgramLike",
        users: list["UserLike"] | None = None,
        email: str | None = None,
        type_: ClassTypeEnum | None = None,
        classes: list["ClassLike"] | None = None,
        description: str | None = None,
    ) -> Class:
        """
        Create a Class via the Hive API.
        """

        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"

        payload: dict[str, object] = {
            "name": name,
            "program": resolve_item_or_id(program),
        }

        # Users list - include always, default to empty list like create_user does for mentees
        if users is None:
            users = []
        payload["users"] = [resolve_item_or_id(u) for u in users]

        # Optional fields
        if email is not None:
            payload["email"] = email
        if type_ is not None:
            payload["type"] = type_.value
        if classes is not None:
            payload["classes"] = [resolve_item_or_id(c) for c in classes]
        if description is not None:
            payload["description"] = description

        response = self.post("/api/core/management/classes/", payload)
        return Class.from_dict(response, hive_client=self)

    def delete_class(self, class_: "ClassLike") -> None:
        self.delete(f"/api/core/management/classes/{resolve_item_or_id(class_)}/")

    def update_class(
        self,
        class_: Class,
        *,
        users_from_classes: Iterable["ClassLike"] | None = None,
    ) -> Class:
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"

        assert isinstance(class_.type_, ClassTypeEnum), "Class must have a valid type!"

        data = self.put(
            f"/api/core/management/classes/{class_.id}/",
            {
                "name": class_.name,
                "program": class_.program_id,
                "users": class_.user_ids,
                "email": class_.email,
                "type": class_.type_.value,
                "description": class_.description,
                "classes": (
                    []
                    if users_from_classes is None
                    else [resolve_item_or_id(x) for x in users_from_classes]
                ),
            },
        )
        return Class.from_dict(data, hive_client=self)

    def import_users_to_class(
        self, to_class: "ClassLike", from_classes: Iterable["ClassLike"]
    ) -> Class:
        to_class_data = (
            to_class if isinstance(to_class, Class) else self.get_class(to_class)
        )
        return self.update_class(to_class_data, users_from_classes=from_classes)
