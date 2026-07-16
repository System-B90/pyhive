"""Utility types and helpers for Hive client mixins."""

from typing import Any, Optional, TypeVar, Union, cast, overload

from ..src.types.core_item import HiveCoreItem

CoreItemTypeT = TypeVar("CoreItemTypeT", bound="HiveCoreItem")


@overload
def resolve_item_or_id(item_or_id: None) -> None: ...


@overload
def resolve_item_or_id(item_or_id: HiveCoreItem | int) -> int: ...


def resolve_item_or_id(
    item_or_id: Union[HiveCoreItem, int, None],
) -> Optional[int]:
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


def assert_mutually_exclusive_filters(
    *args: Any,
    error_message: str = "Filters conflict!",
) -> None:
    """Assert that at most one of the provided filter arguments is set (non-None)."""
    assert sum((0 if x is None else 1) for x in args) <= 1, error_message
