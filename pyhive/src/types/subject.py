"""Defines the Subject type and related functionality for the Hive API Python bindings."""

from typing import TYPE_CHECKING, Any, Generator, Iterable, Mapping, Self, TypeVar, cast

from attrs import define, field

from .core_item import HiveCoreItem
from .enums.sync_status_enum import SyncStatusEnum

if TYPE_CHECKING:
    from ...client import HiveClient
    from .module import Module
    from .program import Program

T = TypeVar("T", bound="Subject")


@define
class Subject(HiveCoreItem):
    """Represents a Subject in the Hive system.

    Attributes:
        hive_client (HiveClient): Reference to the Hive API client.
        id (int): Subject ID.
        symbol (str): Subject symbol.
        parent_program_id (int): ID of the parent Program.
        color (str): Subject color (hex code or name).
        name (str): Display name.
        parent_program_name (str): Name of the parent Program.
        sync_status (SyncStatusEnum): Status of subject synchronization.
        sync_message (str | None): Optional sync error or status message.
        segel_path (str): Staff-accessible path on shared drive.

    """

    hive_client: "HiveClient"
    id: int
    symbol: str
    parent_program_id: int
    color: str
    name: str
    parent_program_name: str
    sync_status: SyncStatusEnum
    sync_message: str | None
    segel_path: str
    segel_brief: str
    _parent_program: "Program | None" = field(init=False, default=None)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the Subject to a dictionary."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "parent_program": self.parent_program_id,
            "color": self.color,
            "name": self.name,
            "parent_program_name": self.parent_program_name,
            "sync_status": self.sync_status.value,
            "sync_message": self.sync_message,
            "segel_path": self.segel_path,
            "segel_brief": self.segel_brief,
        }

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any], hive_client: "HiveClient") -> Self:
        """Deserialize a Subject from a dictionary.

        Args:
            src_dict: A dictionary containing Subject data.
            hive_client: An instance of HiveClient.

        Returns:
            A Subject instance.

        """
        return cls(
            hive_client=hive_client,
            id=src_dict["id"],
            symbol=src_dict["symbol"],
            parent_program_id=src_dict["parent_program"],
            color=src_dict["color"],
            name=src_dict["name"],
            parent_program_name=src_dict["parent_program_name"],
            sync_status=SyncStatusEnum(src_dict["sync_status"]),
            sync_message=cast("str | None", src_dict.get("sync_message")),
            segel_path=src_dict["segel_path"],
            segel_brief=src_dict["segel_brief"],
        )

    @property
    def parent_program(self) -> "Program":
        """Lazily load and return the parent Program.

        Returns:
            Program: The parent program instance.

        """
        if self._parent_program is None:
            self._parent_program = self.hive_client.get_program(self.parent_program_id)
        return self._parent_program

    def get_modules(self) -> Iterable["Module"]:
        """Retrieve all modules associated with this subject.

        Returns:
            Iterable[Module]: Iterable of Module instances.

        """
        return self.hive_client.get_modules(parent_subject__id=self.id)

    def get_module(self, module_name: str) -> "Module":
        """Retrieve a specific module by name within this subject.

        Args:
            module_name (str): The name of the module to retrieve.

        Returns:
            Module: The Module instance if found.

        """
        modules = list(
            self.hive_client.get_modules(
                parent_subject__id=self.id, module_name=module_name
            )
        )
        if len(modules) == 0:
            raise ValueError(
                f"Module '{module_name}' not found in subject '{self.name}'"
            )
        if len(modules) > 1:
            raise ValueError(
                f"Multiple modules named '{module_name}' found in subject '{self.name}'"
            )
        return modules[0]

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Subject):
            return False
        return self.id == value.id and self.parent_program == value.parent_program

    def __lt__(self, value: object) -> bool:
        if not isinstance(value, Subject):
            return NotImplemented
        return self.symbol < value.symbol

    def __iter__(self) -> Generator["Module", None, None]:
        """Allow iteration over this Subject to yield its modules."""
        yield from self.get_modules()

    def __hash__(self) -> int:
        return hash(
            (
                self.id,
                self.parent_program_id,
            )
        )

    def delete(self) -> None:
        self.hive_client.delete_subject(self.id)

    def create_module(
        self,
        name: str,
        order: int,
        segel_brief: str = "",
    ) -> "Module":
        return self.hive_client.create_module(
            name=name, order=order, segel_brief=segel_brief, parent_subject=self
        )


SubjectLike = TypeVar("SubjectLike", Subject, int)
