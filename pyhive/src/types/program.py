"""
Name: program.py
Purpose: Model definition for the Hive Program entity.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from collections.abc import Generator, Iterable
from typing import TYPE_CHECKING, Any, Self, TypeVar

from pydantic import Field, PrivateAttr

from .core_item import HiveCoreItem
from .enums.sync_status_enum import SyncStatusEnum
from .subject import Subject

if TYPE_CHECKING:
    from ...client import HiveClient
    from .class_ import Class
    from .user import User


class Program(HiveCoreItem):
    """
    Course Program entity.

    Attributes:
        id: Unique identifier.
        name: Display name of the program.
        checker_id: User ID of the assigned checker.
        sync_status: Sync status (e.g., Normal, Creating).
        sync_message: Optional sync diagnostic message.
        default_class_id: Optional class ID used as default.
        auto_toilet: Auto-toilet generation enabled.
        hanich_raise_hand: Whether hanich can raise hand.
        auto_schedule: Enable auto-scheduling.
        auto_room: Enable automatic room assignments.
        hanich_day_only: Restrict hanich to day-only usage.
        hanich_work_name: Enable work name customization.
        auto_toilet_count: Number of auto toilets to assign.
        hanich_classes_only: Restrict hanich to classes only.
        hanich_schedule: Whether hanich gets scheduled.
    """

    hive_client: "HiveClient" = Field(exclude=True, repr=False)
    id: int
    name: str
    checker_id: int = Field(alias="checker")
    sync_status: SyncStatusEnum

    sync_message: str | None = Field(default=None)
    default_class_id: int | None = Field(default=None, alias="default_class")

    auto_toilet: bool | None = Field(default=None)
    hanich_raise_hand: bool | None = Field(default=None)
    auto_schedule: bool | None = Field(default=None)
    auto_room: bool | None = Field(default=None)
    hanich_day_only: bool | None = Field(default=None)
    hanich_work_name: bool | None = Field(default=None)
    auto_toilet_count: int | None = Field(default=None)
    hanich_classes_only: bool | None = Field(default=None)
    hanich_schedule: bool | None = Field(default=None)

    _checker: "User | None" = PrivateAttr(default=None)
    _default_class: "Class | None" = PrivateAttr(default=None)

    def __str__(self) -> str:
        return f"<Program[{self.id}] {self.name}>"

    @property
    def checker(self) -> "User":
        """
        Lazily loads and returns the checker (staff member).

        Returns:
            User: The associated checker entity.
        """
        if self._checker is None:
            self._checker = self.hive_client.get_user(self.checker_id)
        return self._checker

    @property
    def default_class(self) -> "Class | None":
        """
        Lazily loads the default class, if set.

        Returns:
            Class | None: The associated default class entity, or None if not set.
        """
        if self._default_class is None and self.default_class_id is not None:
            self._default_class = self.hive_client.get_class(self.default_class_id)
        return self._default_class

    def get_subjects(self) -> Iterable[Subject]:
        """
        Returns all subjects belonging to this program.

        Returns:
            Iterable[Subject]: An iterable collection of subject models.
        """
        return self.hive_client.get_subjects(parent_program__id__in=[self.id])

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        """
        Deserializes a Program instance from a dictionary payload.

        Args:
            src_dict (dict[str, Any]): The raw dictionary from the API response.
            hive_client (HiveClient): The client instance for deferred network operations.

        Returns:
            Self: An instantiated and validated Program model.
        """
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Program):
            return False
        return (
            self.id == value.id
            and self.checker_id == value.checker_id
            and self.name == value.name
        )

    def iter_subjects(self) -> Generator[Subject, None, None]:
        """
        Allows iteration over this Program to yield its subjects.

        Yields:
            Generator[Subject, None, None]: A generator producing Subject instances.
        """
        yield from self.get_subjects()

    def delete(self) -> None:
        """
        Deletes the program using the underlying HiveClient.

        Returns:
            None
        """
        self.hive_client.delete_program(self.id)

    def create_subject(
        self,
        symbol: str,
        name: str,
        color: str,
        segel_brief: str = "",
    ) -> Subject:
        """
        Creates a new subject associated with this program.

        Args:
            symbol (str): The subject's symbolic identifier.
            name (str): The display name of the subject.
            color (str): The UI color code for the subject.
            segel_brief (str, optional): Briefing context for the staff. Defaults to "".

        Returns:
            Subject: The newly created subject model.
        """
        return self.hive_client.create_subject(
            symbol=symbol, name=name, program=self, color=color, segel_brief=segel_brief
        )


ProgramLike = TypeVar("ProgramLike", Program, int)
