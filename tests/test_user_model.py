"""
Name: test_user_model.py
Purpose: Unit tests for the curated User model's tolerance of Hive's ""-for-unset
    enum fields — offline, no live server.
"""

from typing import Any

from pyhive.client import HiveClient
from pyhive.src.types.user import User
from pyhive.types import GenderEnum, StatusEnum

HIVE_URL = "https://hive.example.com"


def _client() -> HiveClient:
    return HiveClient(
        "user",
        "pass",
        HIVE_URL,
        existing_token="tok",
        skip_version_check=True,
    )


def _payload(**overrides: Any) -> dict[str, Any]:
    """A course-user row shaped the way Hive serialises one."""
    data: dict[str, Any] = {
        "id": 1,
        "display_name": "Dana",
        "clearance": 3,
        "gender": "Female",
        "current_assignment_options": [],
        "mentees": [],
        "username": "dana",
        "status": "Present",
        "status_date": "2026-01-14T09:00:00Z",
    }
    data.update(overrides)
    return data


def test_reads_a_fully_populated_user() -> None:
    user = User.from_dict(_payload(), hive_client=_client())

    assert user.gender is GenderEnum.FEMALE
    assert user.status is StatusEnum.PRESENT


def test_empty_enum_strings_are_read_as_unset() -> None:
    """Hive answers "" for an enum field that was never set on the user.

    The spec declares both fields required and enum-typed, so validation used to
    fail — and because listings validate every row, one such user made
    ``get_users()`` raise and took down every caller iterating it.
    """
    user = User.from_dict(
        _payload(gender="", status=""),
        hive_client=_client(),
    )

    assert user.gender is None
    assert user.status is None


def test_missing_enum_fields_are_unset_too() -> None:
    payload = _payload()
    del payload["gender"]
    del payload["status"]

    user = User.from_dict(payload, hive_client=_client())

    assert user.gender is None
    assert user.status is None


def test_a_real_value_is_never_coerced_away() -> None:
    user = User.from_dict(
        _payload(gender="NonBinary", status="Home"),
        hive_client=_client(),
    )

    assert user.gender is GenderEnum.NONBINARY
    assert user.status is StatusEnum.HOME
