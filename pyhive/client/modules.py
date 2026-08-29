"""
Module resource mixin for HiveClient.

Adds methods for listing, retrieving, creating and deleting Module records via
the Hive API. Intended for use as a mixin on the main HiveClient only.
"""

from collections.abc import Iterable
from typing import TYPE_CHECKING, Optional

from ..src.types.module import Module, ModuleLike
from .client_shared import ClientCoreMixin
from .utils import resolve_item_or_id

if TYPE_CHECKING:
    from ..src.types.program import ProgramLike
    from ..src.types.subject import SubjectLike


class ModuleClientMixin(ClientCoreMixin):
    """
    Mixin class providing module-related API methods for HiveClient.

    Methods
    -------
    get_modules(parent_subject__id=None, parent_subject=None, module_name=None, ...)
        List all or filtered modules; supports filtering by subject and parent program.
    get_module(module_id)
        Retrieve a single module record by id.
    create_module(...)
        Create a new module under a parent subject.
    delete_module(module)
        Delete a module by id or instance.
    """

    def get_modules(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        /,
        parent_subject__id: int | None = None,
        parent_subject__parent_program__id__in: list[int] | None = None,
        # Non built-in filters
        parent_subject: Optional["SubjectLike"] = None,
        parent_program: Optional["ProgramLike"] = None,
        module_name: str | None = None,
    ) -> Iterable[Module]:
        """Yield ``Module`` objects, supporting filtering by subject and program."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"

        assert (
            not (
                parent_subject__parent_program__id__in is not None
                and parent_program is not None
            )
        ) or (
            len(parent_subject__parent_program__id__in) == 1
            and parent_subject__parent_program__id__in[0]
            == resolve_item_or_id(parent_program)
        ), "parent_subject__parent_program__id__in and parent_program filters conflict!"

        if parent_program:
            parent_subject__parent_program__id__in = [
                resolve_item_or_id(parent_program)
            ]

        modules: Iterable[Module] = self._get_core_items(
            "/api/core/course/modules/",
            Module,
            parent_subject__parent_program__id__in=parent_subject__parent_program__id__in,
            parent_subject__id=(
                parent_subject__id
                if parent_subject__id is not None
                else resolve_item_or_id(parent_subject)
            ),
        )
        if module_name is not None:
            modules = filter(lambda m: m.name == module_name, modules)
        return modules

    def get_module(self, module_id: int) -> Module:
        """Return a single ``Module`` by its id."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        data = self.get(f"/api/core/course/modules/{module_id}/")
        assert isinstance(data, dict)
        return Module.from_dict(
            data,
            hive_client=self,
        )

    def create_module(
        self,
        name: str,
        parent_subject: "SubjectLike",
        order: int,
        segel_brief: str = "",
    ) -> Module:
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"

        return Module.from_dict(
            self.post(
                "/api/core/course/modules/",
                {
                    "name": name,
                    "parent_subject": resolve_item_or_id(parent_subject),
                    "order": order,
                    "segel_brief": segel_brief,
                },
            ),
            hive_client=self,
        )

    def delete_module(self, module: "ModuleLike") -> None:
        self.delete(f"/api/core/course/modules/{resolve_item_or_id(module)}/")
