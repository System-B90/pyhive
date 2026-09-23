from typing import Literal

import pytest

from pyhive.client import HiveClient
from pyhive.types import Exercise, Module, Program, Subject


def test_get_exercises(client: HiveClient):
    for exercise in client.get_exercises():
        assert exercise is not None
        assert isinstance(exercise, Exercise)


def test_get_exercise_by_id(client: HiveClient):
    all_exercises = list(client.get_exercises())
    if not all_exercises:
        pytest.skip("No exercises available to test.")
    ex = all_exercises[0]
    looked_up = client.get_exercise(ex.id)
    assert looked_up.id == ex.id
    assert looked_up.name == ex.name


@pytest.mark.parametrize(
    "getter_name,filter_arg,attr_name",
    [
        ("get_modules", "parent_module__id", "parent_module_id"),
        ("get_modules", "parent_module", "parent_module_id"),
        ("get_subjects", "parent_module__parent_subject__id", "parent_subject_id"),
        ("get_subjects", "parent_subject", "parent_subject_id"),
    ],
)
def test_get_exercises_by_parent(
    client: HiveClient,
    getter_name: Literal["get_modules", "get_subjects"],
    filter_arg: (
        Literal[
            "parent_module__id",
            "parent_module",
            "parent_module__parent_subject__id",
            "parent_subject",
        ]
    ),
    attr_name: Literal["parent_module_id", "parent_subject_id"],
):
    items = list(getattr(client, getter_name)())
    if not items:
        pytest.skip(f"No {getter_name} available for test.")
    item = items[0]

    filtered = list(
        client.get_exercises(
            **{filter_arg: item if "object" in filter_arg else item.id}
        )
    )
    assert all(getattr(e, attr_name) == item.id for e in filtered) or len(filtered) == 0


def test_get_exercises_by_name(client: HiveClient):
    all_exercises = list(client.get_exercises())
    if not all_exercises:
        pytest.skip("No exercises available for exercise_name test.")
    test_name = all_exercises[0].name
    filtered = list(client.get_exercises(exercise_name=test_name))
    assert all(e.name == test_name for e in filtered)
    if filtered:
        assert isinstance(filtered[0], Exercise)


def test_get_exercises_by_nonexistent_name(client: HiveClient):
    result = list(client.get_exercises(exercise_name="__unlikely_to_exist__"))
    assert len(result) == 0


@pytest.mark.parametrize(
    "conflict_case",
    [
        ("module", "parent_module", "parent_module__id"),
        ("subject", "parent_subject", "parent_module__parent_subject__id"),
    ],
)
def test_exercises_conflict(
    client: HiveClient, conflict_case: Literal["module", "subject"]
):
    name, obj_arg, id_arg = conflict_case
    items = list(getattr(client, f"get_{name}s")())
    if not items:
        pytest.skip(f"No {name}s available for exercise conflict test.")
    item = items[0]

    with pytest.raises(AssertionError):
        list(client.get_exercises(**{obj_arg: item, id_arg: item.id + 1}))


def test_get_exercises_from_program(client: HiveClient, large_program: Program):
    exercises: list[Exercise] = []
    for subject in large_program.get_subjects():
        assert isinstance(subject, Subject)
        for module in subject.get_modules():
            assert isinstance(module, Module)
            for exercise in module.get_exercises():
                assert isinstance(exercise, Exercise)
                assert exercise.parent_module == module
                assert exercise.parent_module.parent_subject == subject
                assert (
                    exercise.parent_module.parent_subject.parent_program
                    == large_program
                )
                exercises.append(exercise)
    expected_exercises = list(
        client.get_exercises(
            parent_module__parent_subject__parent_program__id__in=[large_program.id]
        )
    )
    assert len(exercises) > 0 and len(expected_exercises) > 0, (
        "No exercises found in large program!"
    )

    assert len(exercises) == len(expected_exercises)

    exercises.sort()
    expected_exercises.sort()

    for i in range(len(exercises)):
        assert exercises[i] == expected_exercises[i]
        assert exercises[i].name == expected_exercises[i].name
        assert exercises[i].parent_module_id == expected_exercises[i].parent_module_id
        assert exercises[i].parent_subject_id == expected_exercises[i].parent_subject_id
        assert (
            exercises[i].parent_subject_symbol
            == expected_exercises[i].parent_subject_symbol
        )
