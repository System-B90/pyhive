"""Users mixin for HiveClient.

Provides listing and retrieval of user records from the management API.
"""

from collections.abc import Iterable
from typing import TYPE_CHECKING, Optional

from pyhive.src.types.enums.gender_enum import GenderEnum
from pyhive.src.types.enums.status_enum import StatusEnum

from ..client.utils import resolve_item_or_id
from ..src.types.enums.clearance_enum import ClearanceEnum
from ..src.types.user import User
from .client_shared import ClientCoreMixin

if TYPE_CHECKING:
    from ..src.types.class_ import ClassLike
    from ..src.types.program import ProgramLike
    from ..src.types.queue import QueueLike
    from ..src.types.user import UserLike


class UserClientMixin(ClientCoreMixin):
    """Mixin that exposes user management endpoints (list, get, me)."""

    def get_users(  # pylint: disable=too-many-arguments
        self,
        *,
        classes__id__in: list[int] | None = None,
        clearance__in: list[int] | None = None,
        id__in: list[int] | None = None,
        mentor__id: int | None = None,
        mentor__id__in: list[int] | None = None,
        program__id__in: list[int] | None = None,
        program_checker__id__in: list[int] | None = None,
    ) -> Iterable[User]:
        """Yield users filtered by the provided criteria."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"

        return self._get_core_items(
            "/api/core/management/users/",
            User,
            classes__id__in=classes__id__in,
            clearance__in=clearance__in,
            id__in=id__in,
            mentor__id=mentor__id,
            mentor__id__in=mentor__id__in,
            program__id__in=program__id__in,
            program_checker__id__in=program_checker__id__in,
        )

    def get_user(self, user_id: int) -> User:
        """Return a single user by ``user_id``."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"

        data = self.get(f"/api/core/management/users/{user_id}/")
        assert isinstance(data, dict)
        return User.from_dict(
            data,
            hive_client=self,
        )

    def get_user_me(self) -> User:  # pragma: no cover
        """Return the current user.

        Note: This endpoint is intentionally not implemented because it does not
        return the same shape as ``/users/{id}/`` in the current API.
        """
        raise NotImplementedError("get_user_me() is not implemented")
        # For some reason this endpoint does not return the same data as /users/{id}/
        # return User.from_dict(
        #     self.get("/api/core/management/users/me/"),
        #     hive_client=self,
        # )

    def get_students(
        self,
        *,
        of_mentor: Optional["UserLike"] = None,
        of_class: Optional["ClassLike"] = None,
        of_program: Optional["ProgramLike"] = None,
    ) -> Iterable[User]:
        yield from self.get_users(
            classes__id__in=[resolve_item_or_id(of_class)] if of_class else None,
            clearance__in=[ClearanceEnum.HANICH],
            mentor__id=resolve_item_or_id(of_mentor),
            program__id__in=[resolve_item_or_id(of_program)] if of_program else None,
        )

    def get_user_by_name(
        self,
        name: str,
        *,
        clearance: ClearanceEnum | None = None,
    ) -> User | None:
        all_users = list(
            self.get_users(clearance__in=[clearance] if clearance else None)
        )
        # Try matching full user name
        users_matching_full_name = list(
            filter(
                lambda user: (
                    name
                    in (
                        f"{user.first_name} {user.last_name}",
                        user.display_name,
                        user.username,
                    )
                ),
                all_users,
            )
        )
        if len(users_matching_full_name) == 1:
            # Perfect name match found
            # Note that this might fail on students ["אור דוד", "אור דוד כהן"]
            #  where we want the first student, whose first name happens
            #  to be exactly the full name of the second student
            # TODO: Handle names better?
            return users_matching_full_name[0]

        # Try matching only first name
        users_matching_first_name = list(
            filter(
                lambda user: user.first_name == name,
                all_users,
            )
        )

        if len(users_matching_first_name) > 1:
            raise RuntimeError("More than one user found matching given name!")
        return (
            users_matching_first_name[0] if len(users_matching_first_name) > 0 else None
        )

    def get_student(
        self, name: str | None = None, number: int | None = None
    ) -> User | None:
        if name is None and number is None:
            raise ValueError("Either name or number must be given!")

        if number is None:
            assert name is not None
            return self.get_user_by_name(name, clearance=ClearanceEnum.HANICH)

        assert number is not None

        all_students = list(self.get_students())

        students_matching_number = list(
            filter(lambda student: student.number == number, all_students)
        )

        if len(students_matching_number) == 0:
            return None

        students_perfect_match = []
        if name is not None:
            students_perfect_match = list(
                filter(
                    lambda student: (
                        name
                        in (
                            student.first_name,
                            student.last_name,
                            student.display_name,
                            f"{student.first_name} {student.last_name}",
                        )
                    ),
                    students_matching_number,
                )
            )

        if len(students_perfect_match) > 1:
            raise RuntimeError(
                "More than one student found matching given name and number!"
            )

        return students_perfect_match[0] if len(students_perfect_match) == 1 else None

    def create_user(  # pylint: disable=too-many-arguments, too-many-locals, too-many-branches
        self,
        username: str,
        password: str,
        *,
        clearance: ClearanceEnum,
        gender: GenderEnum,
        number: int | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        mentees: list["UserLike"] | None = None,
        status: StatusEnum = StatusEnum.PRESENT,
        avatar_filename: str | None = None,
        program: Optional["ProgramLike"] = None,
        checkers_brief: str | None = None,
        mentor: Optional["UserLike"] = None,
        classes: list["ClassLike"] | None = None,
        queue: Optional["QueueLike"] = None,
        disable_queue: bool | None = None,
        user_queue: Optional["QueueLike"] = None,
        disable_user_queue: bool | None = None,
        override_queue: Optional["QueueLike"] = None,
        confirmed: bool | None = None,
        teacher: bool | None = None,
        hostname: str | None = None,
    ) -> User:
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"

        payload: dict[str, object] = {
            "username": username,
            "password": password,
            "clearance": clearance,
            "gender": gender,
            "status": status,
        }

        # Only add optional fields if they are not None
        if number is not None:
            payload["number"] = number
        if first_name is not None:
            payload["first_name"] = first_name
        if last_name is not None:
            payload["last_name"] = last_name

        if mentees is None:
            mentees = []
        payload["mentees"] = [resolve_item_or_id(m) for m in mentees]

        if avatar_filename is not None:
            payload["avatar_filename"] = avatar_filename
        if program is not None:
            payload["program"] = resolve_item_or_id(program)
        if checkers_brief is not None:
            payload["checkers_brief"] = checkers_brief
        if mentor is not None:
            payload["mentor"] = resolve_item_or_id(mentor)
        if classes is not None:
            payload["classes"] = [resolve_item_or_id(c) for c in classes]
        if queue is not None:
            payload["queue"] = resolve_item_or_id(queue)
        if disable_queue is not None:
            payload["disable_queue"] = disable_queue
        if user_queue is not None:
            payload["user_queue"] = resolve_item_or_id(user_queue)
        if disable_user_queue is not None:
            payload["disable_user_queue"] = disable_user_queue
        if override_queue is not None:
            payload["override_queue"] = resolve_item_or_id(override_queue)
        if confirmed is not None:
            payload["confirmed"] = confirmed
        if teacher is not None:
            payload["teacher"] = teacher
        if hostname is not None:
            payload["hostname"] = hostname

        # To comply with Hive's "hanich_required_fields" constraint
        if payload.get("clearance", None) != ClearanceEnum.HANICH and (
            any(payload.get(k, None) is not None for k in ("number", "program"))
            or payload.get("teacher", False)
        ):
            raise TypeError(
                "A user which is not a HANICH must not be associated with a program, nor have a number, nor be a teacher!"  # pylint: disable=line-too-long
            )
        if payload.get("clearance", None) == ClearanceEnum.HANICH and (
            any(payload.get(k, None) is None for k in ("number", "program"))
        ):
            raise TypeError(
                "A user which is a HANICH must be associated with a program and have a number!"
            )

        response = self.post("/api/core/management/users/", payload)

        return User.from_dict(response, hive_client=self)

    def delete_user(self, user: "UserLike") -> None:
        self.delete(f"/api/core/management/users/{resolve_item_or_id(user)}/", True)

    def create_student(
        self,
        username: str,
        password: str,
        gender: GenderEnum,
        *,
        number: int | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        program: Optional["ProgramLike"] = None,
        hostname: str | None = None,
        status: StatusEnum = StatusEnum.PRESENT,
        mentor: Optional["UserLike"] = None,
        classes: list["ClassLike"] | None = None,
        avatar_filename: str | None = None,
        checkers_brief: str | None = None,
        queue: Optional["QueueLike"] = None,
        user_queue: Optional["QueueLike"] = None,
        disable_queue: bool | None = None,
        disable_user_queue: bool | None = None,
        override_queue: Optional["QueueLike"] = None,
    ) -> User:
        return self.create_user(
            username=username,
            password=password,
            gender=gender,
            clearance=ClearanceEnum.HANICH,
            number=number,
            first_name=first_name,
            last_name=last_name,
            program=program,
            hostname=hostname,
            status=status,
            mentor=mentor,
            classes=classes,
            avatar_filename=avatar_filename,
            checkers_brief=checkers_brief,
            queue=queue,
            user_queue=user_queue,
            disable_queue=disable_queue,
            disable_user_queue=disable_user_queue,
            override_queue=override_queue,
            teacher=False,
        )

    def update_user(self, user: User) -> User:
        """Commits the local state of the user to the server"""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"

        response = self.put(
            f"/api/core/management/users/{resolve_item_or_id(user)}/",
            user.to_dict(),
        )
        assert isinstance(response, dict)
        return User.from_dict(response, hive_client=self)

    def set_users_queue(self, user: "UserLike", queue: "QueueLike") -> User:
        full_user = user if isinstance(user, User) else self.get_user(user)
        full_user.queue_id = resolve_item_or_id(queue)
        return self.update_user(full_user)
