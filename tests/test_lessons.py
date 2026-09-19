"""
Name: test_lessons.py
Purpose: Offline unit tests for LessonClientMixin, mocked via pytest-httpx.
"""

from typing import Any

from pyhive.client import HiveClient
from pyhive.src.types.lesson import Lesson
from pyhive.src.types.lesson_rule import LessonRule

HIVE_URL = "https://hive.example.com"

LESSON_ID = "11111111-1111-4111-8111-111111111111"
LESSON_RULE_ID = "55555555-5555-4555-8555-555555555555"

LESSON = {
    "id": LESSON_ID,
    "name": "L1",
    "module_id": 2,
    "module_order": "0",
    "module_name": "M",
    "subject_symbol": "S",
    "subject_name": "Subject",
    "program_name": "Program",
}
LESSON_RULE = {"id": LESSON_RULE_ID, "queue_data": None, "student_groups_data": []}


def _client(httpx_mock: Any) -> HiveClient:
    httpx_mock.add_response(
        method="POST",
        url=f"{HIVE_URL}/api/core/token/",
        json={"access": "access-1", "refresh": "refresh-1"},
        status_code=200,
    )
    return HiveClient(
        "user", "pass", HIVE_URL, verify=False, proxy=None, skip_version_check=True
    )


def test_get_lessons(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(url=f"{HIVE_URL}/api/core/schedule/lessons/", json=[LESSON])
    lessons = list(client.get_lessons())
    assert lessons == [Lesson.from_dict(LESSON, hive_client=client)]


def test_get_lesson(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        url=f"{HIVE_URL}/api/core/schedule/lessons/{LESSON_ID}/", json=LESSON
    )
    lesson = client.get_lesson(LESSON_ID)
    assert isinstance(lesson, Lesson)
    assert str(lesson.id) == LESSON_ID


def test_create_lesson(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="POST", url=f"{HIVE_URL}/api/core/schedule/lessons/", json=LESSON
    )
    lesson = client.create_lesson("L1", 2)
    assert isinstance(lesson, Lesson)


def test_update_lesson(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="PATCH",
        url=f"{HIVE_URL}/api/core/schedule/lessons/{LESSON_ID}/",
        json=LESSON,
    )
    updated = client.update_lesson(LESSON_ID, name="L2")
    assert isinstance(updated, Lesson)


def test_delete_lesson(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="DELETE",
        url=f"{HIVE_URL}/api/core/schedule/lessons/{LESSON_ID}/",
        status_code=204,
    )
    client.delete_lesson(LESSON_ID)


def test_get_lesson_rules(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        url=f"{HIVE_URL}/api/core/schedule/lessons/{LESSON_ID}/rules/",
        json=[LESSON_RULE],
    )
    rules = list(client.get_lesson_rules(lesson=LESSON_ID))
    assert rules == [LessonRule.from_dict(LESSON_RULE, hive_client=client)]


def test_create_lesson_rule(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="POST",
        url=f"{HIVE_URL}/api/core/schedule/lessons/{LESSON_ID}/rules/",
        json=LESSON_RULE,
    )
    rule = client.create_lesson_rule(lesson=LESSON_ID, queue=9)
    assert isinstance(rule, LessonRule)


def test_update_lesson_rule(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="PATCH",
        url=f"{HIVE_URL}/api/core/schedule/lessons/{LESSON_ID}/rules/{LESSON_RULE_ID}/",
        json=LESSON_RULE,
    )
    rule = client.update_lesson_rule(lesson=LESSON_ID, rule_id=LESSON_RULE_ID, queue=1)
    assert isinstance(rule, LessonRule)


def test_delete_lesson_rule(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="DELETE",
        url=f"{HIVE_URL}/api/core/schedule/lessons/{LESSON_ID}/rules/{LESSON_RULE_ID}/",
        status_code=204,
    )
    client.delete_lesson_rule(lesson=LESSON_ID, rule_id=LESSON_RULE_ID)
