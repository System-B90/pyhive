import re
from typing import Literal

import pytest

from pyhive.client import HiveClient
from pyhive.src.types.assignment import Assignment
from pyhive.src.types.assignment_response import AssignmentResponse
from pyhive.src.types.class_ import Class
from pyhive.src.types.enums.class_type_enum import ClassTypeEnum
from pyhive.src.types.exercise import Exercise
from pyhive.src.types.form_field import FormField
from pyhive.src.types.user import User
from tests.common import get_client_params


def test_client_url():
    hive_url = "https://hive.org"
    with HiveClient(
        "michaelks", "Password1", hive_url, verify=False, skip_version_check=True
    ) as client:
        assert client.hive_url == hive_url


def test_get_classes(client: HiveClient):
    classes = list(client.get_classes())
    assert len(classes) > 0
    assert all(isinstance(c, Class) for c in classes)


def test_get_classes_with_filters(client: HiveClient):
    # Name filter
    name_filter = "בינוניים"
    filtered = list(client.get_classes(name=name_filter))
    assert all(c.name == name_filter for c in filtered), "Name filter failed"

    # Type filter
    type_filter = ClassTypeEnum.STUDENT_GROUP
    filtered_type = list(client.get_classes(type_=type_filter))
    assert all(c.type_ == type_filter for c in filtered_type), "Type filter failed"


def test_get_class_by_id(client: HiveClient):
    cls = next(iter(client.get_classes()))
    fetched = client.get_class(cls.id)
    assert isinstance(fetched, Class)
    assert fetched.id == cls.id


def test_get_users(client: HiveClient):
    users = list(client.get_users())
    assert len(users) > 0
    assert all(isinstance(u, User) for u in users)


def test_get_user_by_id(client: HiveClient):
    user = next(iter(client.get_users()))
    fetched = client.get_user(user.id)
    assert isinstance(fetched, User)
    assert fetched.id == user.id


def test_get_exercises(client: HiveClient):
    exercises = list(client.get_exercises())
    assert exercises
    assert all(isinstance(e, Exercise) for e in exercises)


def test_get_exercise_by_id(client: HiveClient):
    exercise = next(iter(client.get_exercises()))
    fetched = client.get_exercise(exercise.id)
    assert isinstance(fetched, Exercise)
    assert fetched.id == exercise.id


def test_get_exercise_fields(client: HiveClient):
    exercise = next(iter(client.get_exercises()))
    fields = list(client.get_exercise_fields(exercise))
    assert all(isinstance(f, FormField) for f in fields)


def test_get_exercise_field_by_id(client: HiveClient):
    found = False
    for exercise in client.get_exercises():
        for field in client.get_exercise_fields(exercise):
            fetched = client.get_exercise_field(exercise, field.id)
            assert isinstance(fetched, FormField)
            assert fetched.id == field.id
            assert field == fetched
            found = True
    assert found, "No exercise fields available to test."


def test_get_assignments(client: HiveClient):
    assignments = list(client.get_assignments())
    assert all(isinstance(a, Assignment) for a in assignments)
    assert all(isinstance(a.exercise, Exercise) for a in assignments)


@pytest.mark.xfail(strict=False, reason="No assignments seeded yet")
def test_get_assignment_by_id(client: HiveClient):
    assignment = next(iter(client.get_assignments()))
    fetched = client.get_assignment(assignment.id)
    assert isinstance(fetched, Assignment)
    assert fetched.id == assignment.id


@pytest.mark.xfail(strict=False, reason="No assignments seeded yet")
def test_get_assignment_responses(client: HiveClient):
    assignment = next(iter(client.get_assignments()))
    responses = list(client.get_assignment_responses(assignment))
    assert all(isinstance(r, AssignmentResponse) for r in responses)


@pytest.mark.xfail(strict=False, reason="No assignments seeded yet")
def test_get_assignment_response_by_id(client: HiveClient):
    assignment = next(iter(client.get_assignments()))
    responses = list(client.get_assignment_responses(assignment))
    if responses:
        resp = client.get_assignment_response(assignment, responses[0].id)
        assert isinstance(resp, AssignmentResponse)
        assert resp.id == responses[0].id


@pytest.mark.parametrize(
    "kwargs",
    [
        {"user__mentor__id": 1, "user__mentor__id__in": [1]},
        {"user__mentor__id": 1, "for_mentees_of": 1},
        {"user__mentor__id__in": [1], "for_mentees_of": 1},
    ],
)
def test_assignments_conflict_mentor_filters(client: HiveClient, kwargs):
    with pytest.raises(AssertionError):
        list(client.get_assignments(**kwargs))


@pytest.mark.parametrize(
    "conflict_case",
    [
        ("module", "parent_module", "exercise__parent_module__id"),
        ("subject", "parent_subject", "exercise__parent_module__parent_subject__id"),
        ("user_classes", "user__classes__id", "user__classes__id__in"),
        ("user_id", "user__id__in", "for_user"),
    ],
)
def test_assignments_conflicts(
    client: HiveClient,
    conflict_case: (
        Literal["module"]
        | Literal["subject"]
        | Literal["user_classes"]
        | Literal["user_id"]
    ),
):
    name, arg1, arg2 = conflict_case

    if name in ("module", "subject"):
        items = list(getattr(client, f"get_{name}s")())
        assert items
        item = items[0]
        with pytest.raises(AssertionError):
            list(client.get_assignments(**{arg1: item, arg2: getattr(item, "id") + 1}))
    elif name == "user_id":
        with pytest.raises(AssertionError):
            list(client.get_assignments(**{arg1: [5], arg2: 1}))
    else:  # user_classes
        with pytest.raises(AssertionError):
            list(client.get_assignments(**{arg1: 1, arg2: [1, 2]}))


def test_get_hive_version(client: HiveClient):
    version = client.get_hive_version()
    assert isinstance(version, str)
    assert re.match(r"^\d+\.\d+\.\d+", version)


def test_invalid_hive_version_raises(monkeypatch: pytest.MonkeyPatch):
    from pyhive.src.api_versions import LATEST_API_VERSION, MIN_API_VERSION

    invalid = "0.0.0-unsupported"
    monkeypatch.setattr(HiveClient, "get_hive_version", lambda self: invalid)
    params = get_client_params()
    params["skip_version_check"] = False
    with pytest.raises(RuntimeError) as exc:
        HiveClient(**params)
    msg = str(exc.value)
    assert f"Unsupported Hive API version '{invalid}'" in msg
    assert f"{MIN_API_VERSION} .. {LATEST_API_VERSION}" in msg


def test_skip_version_check(monkeypatch: pytest.MonkeyPatch):
    invalid = "0.0.0-unsupported"
    monkeypatch.setattr(HiveClient, "get_hive_version", lambda self: invalid)
    # Should not raise when skip_version_check=True
    params = get_client_params()
    params["skip_version_check"] = True
    with HiveClient(**params) as client2:
        assert client2 is not None
