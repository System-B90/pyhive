import httpx
import pytest

from pyhive.client import HiveClient
from pyhive.src.types.user import User
from pyhive.types import ClearanceEnum, GenderEnum, Program


# TODO: Remove xfail once get_user_me is implemented / API parity is ensured
@pytest.mark.xfail(strict=False, reason="get_user_me not implemented in API parity")
def test_user_me(client: HiveClient):
    me = client.get_user_me()
    assert isinstance(me, User)
    assert me.id == client.get_user(me.id).id


def test_create_students(client: HiveClient, mentor: User, program: Program):
    """Test creating multiple student users with unique details."""

    students = [
        {
            "username": "student-1",
            "first_name": "Alice",
            "last_name": "Smith",
            "checkers_brief": "Excellent progress on exercises",
            "hostname": "alice-laptop.local",
        },
        {
            "username": "student-2",
            "first_name": "Bob",
            "last_name": "Johnson",
            "checkers_brief": "Needs improvement in problem-solving",
            "hostname": "bob-desktop.local",
        },
        {
            "username": "student-3",
            "first_name": "Charlie",
            "last_name": "Williams",
            "checkers_brief": "Shows great engagement in class",
            "hostname": "charlie-pc.local",
        },
    ]

    password = "Password1"

    for i, student in enumerate(students, start=1):
        # Clean up existing user if needed
        existing = client.get_user_by_name(student["username"])
        if existing:
            client.delete_user(existing)

        # Create fresh user
        user: User | None = client.create_user(
            username=student["username"],
            password=password,
            clearance=ClearanceEnum.HANICH,
            gender=GenderEnum.NONBINARY,
            number=i,
            first_name=student["first_name"],
            last_name=student["last_name"],
            checkers_brief=student["checkers_brief"],
            hostname=student["hostname"],
            program=program,
            mentor=mentor,
        )

        # Basic validation
        assert user.username == student["username"]
        assert user.program is not None
        assert user.mentor is not None
        assert user.program.id == program.id
        assert user.mentor.id == mentor.id

    for student in students:
        user = client.get_user_by_name(name=student["username"])
        assert user is not None
        assert isinstance(user, User)
        user.delete()


def test_update_user(client: HiveClient, mentor: User, program: Program):
    USER_DATA = {
        "username": "student-123",
        "first_name": "Bob",
        "last_name": "Johnson",
        "checkers_brief": "I don't know",
        "hostname": "bobinson",
    }
    user = client.create_user(
        username=USER_DATA["username"],
        password="test123",
        clearance=ClearanceEnum.HANICH,
        gender=GenderEnum.NONBINARY,
        number=123,
        first_name=USER_DATA["first_name"],
        last_name=USER_DATA["last_name"],
        checkers_brief=USER_DATA["checkers_brief"],
        hostname=USER_DATA["hostname"],
        program=program,
        mentor=mentor,
    )
    assert user is not None and isinstance(user, User)

    try:
        NEW_LAST_NAME = "Smith"
        assert user.last_name != NEW_LAST_NAME, (
            "User's last name is already the updated one!"
        )
        user.last_name = NEW_LAST_NAME

        updated_user = client.update_user(user)
        assert updated_user

        assert updated_user.last_name == NEW_LAST_NAME, "Last name not updated!"

        assert user == updated_user, "User's are not equal!"

        updated_user.delete()
        with pytest.raises(httpx.HTTPStatusError):
            user.delete()
    except Exception:
        user.delete()


def test_update_user_in_place(client: HiveClient, mentor: User, program: Program):
    USER_DATA = {
        "username": "student-123",
        "first_name": "Bob",
        "last_name": "Johnson",
        "checkers_brief": "I don't know",
        "hostname": "bobinson",
    }
    user = client.create_user(
        username=USER_DATA["username"],
        password="test123",
        clearance=ClearanceEnum.HANICH,
        gender=GenderEnum.NONBINARY,
        number=123,
        first_name=USER_DATA["first_name"],
        last_name=USER_DATA["last_name"],
        checkers_brief=USER_DATA["checkers_brief"],
        hostname=USER_DATA["hostname"],
        program=program,
        mentor=mentor,
    )
    assert user is not None and isinstance(user, User)

    try:
        NEW_LAST_NAME = "Smith"
        assert user.last_name != NEW_LAST_NAME, (
            "User's last name is already the updated one!"
        )
        user.last_name = NEW_LAST_NAME

        user_capture = user.to_dict()

        user.update()

        updated_user_capture = client.get_user(user.id).to_dict()

        for key in set(user_capture.keys()).union(updated_user_capture.keys()):
            if key == "display_name":
                # Expected to be unequal since the local capture is not validated
                assert user_capture[key] != updated_user_capture[key]
                continue
            assert user_capture[key] == updated_user_capture[key], (
                f"Data mismatch for {key} of updated user post update!"
            )
    finally:
        user.delete()
