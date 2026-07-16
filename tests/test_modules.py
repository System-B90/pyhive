import random
import time
from typing import Any, Optional

import pytest

from pyhive.client import HiveClient
from pyhive.types import Exercise, Module, Program, Subject
from tests.common import EXERCISE_DATA_LIST


@pytest.mark.usefixtures("client")
def test_get(client: HiveClient) -> None:
    modules = list(client.get_modules())
    assert len(modules) > 0, "No modules available to test!"
    assert all(
        module is not None and isinstance(module, Module) for module in modules
    ), "Module in modules is not of a valid form!"


@pytest.mark.usefixtures("module")
def test_module_exercises(module: Module) -> None:
    module.create_exercise(**EXERCISE_DATA_LIST[0])
    exercises = list(module.get_exercises())
    assert len(exercises) > 0, "No exercises available to test!"
    assert all(isinstance(exercise, Exercise) for exercise in exercises)
    for exercise in exercises:
        assert exercise.parent_module_id == module.id
        assert exercise.parent_module_name == module.name
        assert exercise.parent_module_order == module.order
        assert exercise.parent_subject_id == module.parent_subject_id
        assert exercise.parent_subject_name == module.parent_subject_name
        assert exercise.parent_subject_symbol == module.parent_subject_symbol
        assert exercise.parent_module.parent_subject == module.parent_subject


@pytest.mark.usefixtures("client")
def test_get_module_by_name(client: HiveClient):
    MODULE_NAME = "כחול לבן"
    modules = list(client.get_modules(module_name=MODULE_NAME))
    assert len(modules) == 1, f"Expected exactly one module with name '{MODULE_NAME}'"
    module = modules[0]
    assert isinstance(module, Module)
    assert module.name == MODULE_NAME
    assert module.parent_subject_name == "Apple"
    assert module.parent_subject_symbol == "A"


@pytest.mark.usefixtures("client")
def test_get_modules_by_subject_id(client: HiveClient) -> None:
    all_subjects = list(client.get_subjects())
    assert len(all_subjects) > 0, "No subjects available for parent_subject__id test."
    sub_id = all_subjects[0].id
    filtered = list(client.get_modules(parent_subject__id=sub_id))
    assert (
        all(
            hasattr(m, "parent_subject_id") and m.parent_subject_id == sub_id
            for m in filtered
        )
        or len(filtered) == 0
    )


@pytest.mark.usefixtures("client")
def test_get_modules_by_subject_object(client: HiveClient):
    all_subjects = list(client.get_subjects())
    assert len(all_subjects) > 0, "No subjects available for parent_subject test."
    subject = all_subjects[0]
    filtered = list(client.get_modules(parent_subject=subject))
    assert (
        all(
            hasattr(m, "parent_subject_id") and m.parent_subject_id == subject.id
            for m in filtered
        )
        or len(filtered) == 0
    )


@pytest.mark.usefixtures("client")
def test_get_modules_by_subject_program_id(client: HiveClient) -> None:
    all_subjects: list[Subject] = list(client.get_subjects())
    assert len(all_subjects) > 0, (
        "No subjects available for parent_subject__parent_program__id__in test."
    )
    program_id = all_subjects[0].parent_program_id
    assert program_id is not None, (
        "No program_id found in subjects for module relationship test."
    )
    filtered: list[Module] = list(
        client.get_modules(parent_subject__parent_program__id__in=[program_id])
    )
    assert len(filtered) > 0, f"No modules found under parent program {program_id}"
    assert all(x.parent_subject.parent_program_id == program_id for x in filtered), (
        "Mismatched module found under program search!"
    )


@pytest.mark.usefixtures("client")
def test_get_modules_by_name(client: HiveClient) -> None:
    all_modules = list(client.get_modules())
    assert len(all_modules) > 0, "No modules available for module_name test."
    module_name = all_modules[0].name
    filtered = list(client.get_modules(module_name=module_name))
    assert all(m.name == module_name for m in filtered)
    if filtered:
        assert isinstance(filtered[0], Module)


@pytest.mark.usefixtures("client")
def test_get_modules_by_nonexistent_name(client: HiveClient):
    result = list(client.get_modules(module_name="__unlikely_to_exist__"))
    assert len(result) == 0


@pytest.mark.usefixtures("client")
def test_get_modules_by_program(
    client: HiveClient, program: Program, subject: Subject
) -> None:
    for i in range(5):
        client.create_module(
            f"TestModule{i}{str(int(time.time()))[:3]}{random.randint(100, 999)}",
            subject,
            i,
        )

    modules = list(client.get_modules(parent_program=program))
    assert len(modules) > 0, f"No modules found under {program}"
    assert all(
        (
            isinstance(module, Module)
            and (module.parent_program_name == program.name)
            and (module.parent_subject.parent_program_id == program.id)
        )
        for module in modules
    )


@pytest.mark.usefixtures("client")
def test_modules_conflict_parent_program_filters_mismatch(
    client: HiveClient, program: Program
):
    with pytest.raises(AssertionError):
        list(
            client.get_modules(
                parent_subject__parent_program__id__in=[program.id + 98765],
                parent_program=program,
            )
        )


@pytest.mark.usefixtures("client")
def test_modules_both_program_filters_match_allowed(
    client: HiveClient, program: Program
):
    modules = list(
        client.get_modules(
            parent_subject__parent_program__id__in=[program.id],
            parent_program=program,
        )
    )
    assert isinstance(modules, list)


@pytest.mark.parametrize("exercise_data", EXERCISE_DATA_LIST)
def test_create_exercise_in_module(module: Module, exercise_data: dict[str, Any]):
    exercise: Optional[Exercise] = None
    try:
        exercise = module.create_exercise(**exercise_data)
        assert exercise.parent_module == module
        assert exercise.parent_module_id == module.id
    finally:
        if exercise is not None:
            exercise.delete()


def test_create_exercises_in_module(module: Module):
    exercises: list[Exercise] = []
    try:
        for exercise_data in EXERCISE_DATA_LIST:
            exercise = module.create_exercise(**exercise_data)
            assert exercise.parent_module == module
            assert exercise.parent_module_id == module.id
            exercises.append(exercise)
    finally:
        for exercise in exercises:
            exercise.delete()
