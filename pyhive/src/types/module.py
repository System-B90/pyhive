"""Module model definition for the Hive system.

Represents a logical course module within a subject, supporting serialization,
lazy loading of parent subject, and retrieval of exercises.
"""

from typing import (
    TYPE_CHECKING,
    Any,
    Generator,
    Iterable,
    Mapping,
    Optional,
    Self,
    TypeVar,
    cast,
)

from attrs import define, field

from .enums.exercise_patbas_enum import PatbasEnum
from .enums.exercise_preview_types import ExercisePreviewTypes
from .enums.sync_status_enum import SyncStatusEnum
from .exercise import Exercise
from .program import HiveCoreItem

if TYPE_CHECKING:
    from ...client import HiveClient
    from .subject import Subject

T = TypeVar("T", bound="Module")


@define
class Module(HiveCoreItem):
    """Course Subject Module.

    Attributes:
        id: Unique identifier.
        name: Name of the module.
        parent_subject_id: ID of the parent subject.
        order: Order of display within the subject.
        sync_status: Synchronization status.
        sync_message: Optional error or status message.
        parent_program_name: Name of the program the subject belongs to.
        parent_subject_name: Name of the parent subject.
        parent_subject_symbol: Symbol of the parent subject.
        segel_path: Network path accessible to staff.

    """

    hive_client: "HiveClient"
    id: int
    name: str
    parent_subject_id: int
    order: str
    sync_status: SyncStatusEnum
    sync_message: None | str
    parent_program_name: str
    parent_subject_name: str
    parent_subject_symbol: str
    segel_path: str

    _parent_subject: "Subject | None" = field(init=False, default=None)

    @property
    def parent_subject(self) -> "Subject":
        """Lazily load and return the parent subject."""
        if self._parent_subject is None:
            self._parent_subject = self.hive_client.get_subject(self.parent_subject_id)
        return self._parent_subject

    def to_dict(self) -> dict[str, Any]:
        """Serialize the module to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "parent_subject": self.parent_subject_id,
            "order": self.order,
            "sync_status": self.sync_status.value,
            "sync_message": self.sync_message,
            "parent_program_name": self.parent_program_name,
            "parent_subject_name": self.parent_subject_name,
            "parent_subject_symbol": self.parent_subject_symbol,
            "segel_path": self.segel_path,
        }

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any], hive_client: "HiveClient") -> Self:
        """Deserialize a module from a dictionary."""
        d = dict(src_dict)
        return cls(
            hive_client=hive_client,
            id=d["id"],
            name=d["name"],
            parent_subject_id=d["parent_subject"],
            order=d["order"],
            sync_status=SyncStatusEnum(d["sync_status"]),
            sync_message=cast("None | str", d["sync_message"]),
            parent_program_name=d["parent_program_name"],
            parent_subject_name=d["parent_subject_name"],
            parent_subject_symbol=d["parent_subject_symbol"],
            segel_path=d["segel_path"],
        )

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Module):
            return False
        return self.id == value.id and self.parent_subject == value.parent_subject

    def __lt__(self, value: object) -> bool:
        if not isinstance(value, Module):
            return NotImplemented
        return self.order < value.order

    def get_exercises(self) -> Iterable[Exercise]:
        """Fetch all exercises within this module."""
        return self.hive_client.get_exercises(parent_module__id=self.id)

    def get_exercise(self, exercise_name: str) -> Exercise:
        """Fetch a specific exercise by name within this module."""
        exercises = list(
            self.hive_client.get_exercises(
                parent_module__id=self.id,
                exercise_name=exercise_name,
            )
        )

        if len(exercises) == 0:
            raise ValueError(
                f"Exercise '{exercise_name}' not found in module '{self.name}'"
            )
        if len(exercises) > 1:
            raise ValueError(
                f"Multiple exercises named '{exercise_name}' found in module '{self.name}'"
            )
        return exercises[0]

    def __iter__(self) -> Generator["Exercise", None, None]:
        """Allow iteration over this Module to yield its exercises."""
        yield from self.get_exercises()

    def __hash__(self) -> int:
        return hash(
            (
                self.id,
                self.parent_subject_id,
            )
        )

    def delete(self) -> None:
        self.hive_client.delete_module(self)

    def create_exercise(
        self,
        name: str,
        order: int,
        *,
        download: bool = False,
        preview: ExercisePreviewTypes = ExercisePreviewTypes.DISABLED,
        patbas_preview: ExercisePreviewTypes = ExercisePreviewTypes.DISABLED,
        style: str = "",
        patbas_download: bool = False,
        patbas: PatbasEnum = PatbasEnum.NEVER,
        on_creation_data: str = "",
        autocheck_tag: str = "",
        autodone: bool = False,
        expected_duration: str = "",
        segel_brief: str = "",
        is_lecture: bool = False,
        tags: Optional[list[str]] = None,
    ) -> Exercise:
        return self.hive_client.create_exercise(
            name=name,
            order=order,
            parent_module=self,
            download=download,
            preview=preview,
            patbas_preview=patbas_preview,
            style=style,
            patbas_download=patbas_download,
            patbas=patbas,
            on_creation_data=on_creation_data,
            autocheck_tag=autocheck_tag,
            autodone=autodone,
            expected_duration=expected_duration,
            segel_brief=segel_brief,
            is_lecture=is_lecture,
            tags=tags,
        )


ModuleLike = TypeVar("ModuleLike", Module, int)
