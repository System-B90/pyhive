"""Utility types and helpers for Hive client mixins."""

from typing import Any, TypeVar, cast, overload
from uuid import UUID

from ..src.types.core_item import HiveCoreItem

CoreItemTypeT = TypeVar("CoreItemTypeT", bound="HiveCoreItem")

UUIDLike = UUID | str | int
""" A UUID primary key or its string form (Hive >= 7.3.0), or an integer id (older Hive). """


@overload
def resolve_item_or_id(item_or_id: None) -> None: ...


@overload
def resolve_item_or_id(item_or_id: HiveCoreItem | int) -> int: ...


def resolve_item_or_id(
    item_or_id: HiveCoreItem | int | None,
) -> int | None:
    """Return the integer id represented by ``item_or_id``.

    If ``item_or_id`` is ``None``, returns ``None``. If a ``HiveCoreItem`` is provided, its ``id`` is returned.
    If an ``int`` is provided, it is returned as-is.
    """
    if item_or_id is None:
        return None
    if not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
        item_or_id, (HiveCoreItem, int)
    ):
        raise TypeError(
            f"Expected HiveCoreItem or int, got {type(item_or_id).__name__}"
        )
    return (
        cast(
            int,
            item_or_id.id,  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
        )
        if isinstance(item_or_id, HiveCoreItem) and hasattr(item_or_id, "id")
        else cast(int, item_or_id)
    )


@overload
def resolve_item_or_uuid(item_or_id: None) -> None: ...


@overload
def resolve_item_or_uuid(item_or_id: "HiveCoreItem | UUIDLike") -> UUID | int: ...


def resolve_item_or_uuid(
    item_or_id: "HiveCoreItem | UUIDLike | None",
) -> UUID | int | None:
    """Return the UUID (or pre-7.3.0 integer id) represented by ``item_or_id``.

    If ``item_or_id`` is ``None``, returns ``None``. If a ``HiveCoreItem`` is provided, its ``id`` is returned.
    """
    if item_or_id is None:
        return None
    if isinstance(item_or_id, HiveCoreItem):
        item_id = getattr(item_or_id, "id", None)
        if item_id is None:
            raise ValueError(f"{type(item_or_id).__name__} has no id")
        item_or_id = cast(UUIDLike, item_id)
    if isinstance(item_or_id, UUID | int):
        return item_or_id
    if isinstance(item_or_id, str):  # pyright: ignore[reportUnnecessaryIsInstance]
        return int(item_or_id) if item_or_id.isdigit() else UUID(item_or_id)
    raise TypeError(
        f"Expected HiveCoreItem, UUID, str or int, got {type(item_or_id).__name__}"
    )


def assert_mutually_exclusive_filters(
    *args: Any,
    error_message: str = "Filters conflict!",
) -> None:
    """Assert that at most one of the provided filter arguments is set (non-None)."""
    assert sum((0 if x is None else 1) for x in args) <= 1, error_message
