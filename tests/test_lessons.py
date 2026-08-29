"""
Name: test_lessons.py
Purpose: Offline unit tests for LessonClientMixin, mocked via pytest-httpx.
"""

from typing import Any

from pyhive.client import HiveClient
from pyhive.src.types.lesson import Lesson
from pyhive.src.types.lesson_rule import LessonRule

HIVE_URL = "https://hive.example.com"

LESSON = {
    "id": 1,
    "name": "L1",
    "module_id": 2,
    "module_order": "0",
    "module_name": "M",
    "subject_symbol": "S",
    "subject_name": "Subject",
    "program_name": "Program",
}
LESSON_RULE = {"id": 5, "queue_data": None, "student_groups_data": []}


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
    httpx_mock.add_response(url=f"{HIVE_URL}/api/core/schedule/lessons/1/", json=LESSON)
    lesson = client.get_lesson(1)
    assert isinstance(lesson, Lesson)
    assert lesson.id == 1


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
        method="PATCH", url=f"{HIVE_URL}/api/core/schedule/lessons/1/", json=LESSON
    )
    updated = client.update_lesson(1, name="L2")
    assert isinstance(updated, Lesson)


def test_delete_lesson(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="DELETE", url=f"{HIVE_URL}/api/core/schedule/lessons/1/", status_code=204
    )
    client.delete_lesson(1)


def test_get_lesson_rules(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        url=f"{HIVE_URL}/api/core/schedule/lessons/1/rules/", json=[LESSON_RULE]
    )
    rules = list(client.get_lesson_rules(lesson=1))
    assert rules == [LessonRule.from_dict(LESSON_RULE, hive_client=client)]


def test_create_lesson_rule(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="POST",
        url=f"{HIVE_URL}/api/core/schedule/lessons/1/rules/",
        json=LESSON_RULE,
    )
    rule = client.create_lesson_rule(lesson=1, queue=9)
    assert isinstance(rule, LessonRule)


def test_update_lesson_rule(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="PATCH",
        url=f"{HIVE_URL}/api/core/schedule/lessons/1/rules/5/",
        json=LESSON_RULE,
    )
    rule = client.update_lesson_rule(lesson=1, rule_id=5, queue=1)
    assert isinstance(rule, LessonRule)


def test_delete_lesson_rule(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="DELETE",
        url=f"{HIVE_URL}/api/core/schedule/lessons/1/rules/5/",
        status_code=204,
    )
    client.delete_lesson_rule(lesson=1, rule_id=5)
