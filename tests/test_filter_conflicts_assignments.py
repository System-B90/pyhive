"""
Name: test_assignments_conflict.py
Purpose: Tests for conflicting filter parameters in HiveClient assignment retrieval.
Created: 2026-03-29
Author: Michael K. Steinberg
"""

import pytest
from pyhive.client import HiveClient


def test_assignments_conflict_module_id_and_object_mismatch(client: HiveClient):
    modules = list(client.get_modules())
    assert len(modules) > 0, "No modules available for assignment conflict tests."
    module = modules[0]

    with pytest.raises(AssertionError):
        list(
            client.get_assignments(
                parent_module=module, exercise__parent_module__id=module.id + 1
            )
        )


def test_assignments_conflict_subject_id_and_object_mismatch(client: HiveClient):
    subjects = list(client.get_subjects())
    assert len(subjects) > 0, "No subjects available for assignment conflict tests."
    subject = subjects[0]

    with pytest.raises(AssertionError):
        list(
            client.get_assignments(
                parent_subject=subject,
                exercise__parent_module__parent_subject__id=subject.id + 1,
            )
        )


def test_assignments_conflict_user_classes_id_and_id_in(client: HiveClient):
    with pytest.raises(AssertionError):
        list(
            client.get_assignments(
                user__classes__id=1,
                user__classes__id__in=[1, 2],
            )
        )


def test_assignments_conflict_user_id_in_and_for_user_mismatch(client: HiveClient):
    users = list(client.get_users())
    assert len(users) > 0, "No users available for assignment conflict tests."
    user = users[0]

    with pytest.raises(AssertionError):
        list(
            client.get_assignments(
                user__id__in=[user.id + 1],
                for_user=user,
            )
        )


def test_assignments_conflict_mentor_filters_any_two(client: HiveClient):
    # Any two of these should conflict
    with pytest.raises(AssertionError):
        list(client.get_assignments(user__mentor__id=1, user__mentor__id__in=[1]))

    with pytest.raises(AssertionError):
        list(client.get_assignments(user__mentor__id=1, for_mentees_of=1))

    with pytest.raises(AssertionError):
        list(client.get_assignments(user__mentor__id__in=[1], for_mentees_of=1))
