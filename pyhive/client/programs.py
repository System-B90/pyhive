"""
Program resource mixin for HiveClient.

Provides methods for listing, retrieving, creating and deleting Program
records via the Hive API. Designed to be mixed into the main HiveClient only.
"""

from collections.abc import Iterable
from typing import TYPE_CHECKING, Optional

from ..src.types.program import Program, ProgramLike
from .client_shared import ClientCoreMixin
from .utils import resolve_item_or_id

if TYPE_CHECKING:
    from ..src.types.class_ import ClassLike
    from ..src.types.user import UserLike


class ProgramClientMixin(ClientCoreMixin):
    """
    Mixin class adding program-related API methods to the HiveClient.

    Methods
    -------
    get_programs(id__in=None, program_name=None)
        List all or filtered programs via the Hive API.
    get_program(program_id)
        Retrieve a single program record by its id.
    create_program(...)
        Create a new program.
    delete_program(program)
        Delete a program by id or instance.
    """

    def get_programs(
        self,
        id__in: list[int] | None = None,
        program_name: str | None = None,
    ) -> Iterable[Program]:
        """Yield ``Program`` objects, optionally filtered by ids/name."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"

        programs: Iterable[Program] = self._get_core_items(
            "/api/core/course/programs/",
            Program,
            id__in=id__in,
        )
        if program_name is not None:
            programs = list(filter(lambda p: p.name == program_name, programs))
        yield from programs

    def get_program(self, program_id: int) -> Program:
        """Return a single ``Program`` by its id."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        data = self.get(f"/api/core/course/programs/{program_id}/")
        assert isinstance(data, dict)
        return Program.from_dict(
            data,
            hive_client=self,
        )

    def create_program(
        self,
        name: str,
        *,
        checker: "UserLike",
        default_class: Optional["ClassLike"] = None,
        auto_toilet: bool | None = None,
        hanich_raise_hand: bool | None = None,
        auto_schedule: bool | None = None,
        auto_room: bool | None = None,
        hanich_day_only: bool | None = None,
        hanich_work_name: bool | None = None,
        auto_toilet_count: int | None = None,
        hanich_classes_only: bool | None = None,
        hanich_schedule: bool | None = None,
    ) -> Program:
        """
        Create a Program via the Hive API.
        """

        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"

        payload: dict[str, object] = {
            "name": name,
            "checker": resolve_item_or_id(checker),
        }

        # Optional fields (only include if not None)
        if default_class is not None:
            payload["default_class"] = resolve_item_or_id(default_class)
        if auto_toilet is not None:
            payload["auto_toilet"] = auto_toilet
        if hanich_raise_hand is not None:
            payload["hanich_raise_hand"] = hanich_raise_hand
        if auto_schedule is not None:
            payload["auto_schedule"] = auto_schedule
        if auto_room is not None:
            payload["auto_room"] = auto_room
        if hanich_day_only is not None:
            payload["hanich_day_only"] = hanich_day_only
        if hanich_work_name is not None:
            payload["hanich_work_name"] = hanich_work_name
        if auto_toilet_count is not None:
            payload["auto_toilet_count"] = auto_toilet_count
        if hanich_classes_only is not None:
            payload["hanich_classes_only"] = hanich_classes_only
        if hanich_schedule is not None:
            payload["hanich_schedule"] = hanich_schedule

        response = self.post("/api/core/course/programs/", payload)

        return Program.from_dict(response, hive_client=self)

    def delete_program(self, program: "ProgramLike") -> None:
        self.delete(f"/api/core/course/programs/{resolve_item_or_id(program)}/")
