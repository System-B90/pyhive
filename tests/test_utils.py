"""
Name: test_utils.py
Purpose: Unit tests for pyhive/client/utils.py — resolve_item_or_id and
    assert_mutually_exclusive_filters.
"""

import pytest

from pyhive.client.utils import assert_mutually_exclusive_filters, resolve_item_or_id
from pyhive.src.types.core_item import HiveCoreItem


class _Item(HiveCoreItem):
    id: int


def test_resolve_item_or_id_with_none_returns_none():
    assert resolve_item_or_id(None) is None


def test_resolve_item_or_id_with_int_passes_through():
    assert resolve_item_or_id(7) == 7


def test_resolve_item_or_id_with_core_item_returns_id():
    assert resolve_item_or_id(_Item(id=42)) == 42


def test_resolve_item_or_id_with_invalid_type_raises_type_error():
    with pytest.raises(TypeError, match="Expected HiveCoreItem or int"):
        resolve_item_or_id("not-valid")  # type: ignore[arg-type]


def test_assert_mutually_exclusive_filters_zero_set_ok():
    assert_mutually_exclusive_filters(None, None)


def test_assert_mutually_exclusive_filters_one_set_ok():
    assert_mutually_exclusive_filters(1, None)


def test_assert_mutually_exclusive_filters_two_set_raises():
    with pytest.raises(AssertionError, match="Filters conflict!"):
        assert_mutually_exclusive_filters(1, 2)


def test_assert_mutually_exclusive_filters_custom_message():
    with pytest.raises(AssertionError, match="custom message"):
        assert_mutually_exclusive_filters(1, 2, error_message="custom message")
