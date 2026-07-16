from typing import Literal, LiteralString

import pytest

from pyhive.client import HiveClient
from pyhive.types import Program, Subject


def test_get_subjects(client: HiveClient):
    for subject in client.get_subjects():
        assert subject is not None
        assert isinstance(subject, Subject)


def test_get_subject_by_id(client: HiveClient):
    all_subjects = list(client.get_subjects())
    if not all_subjects:
        pytest.skip("No subjects available for testing.")
    subj = all_subjects[0]
    looked_up = client.get_subject(subj.id)
    assert looked_up.id == subj.id
    assert looked_up.name == subj.name


def test_get_subjects_by_name(client: HiveClient):
    all_subjects = list(client.get_subjects())
    if not all_subjects:
        pytest.skip("No subjects available for testing.")
    test_name = all_subjects[0].name
    filtered = list(client.get_subjects(subject_name=test_name))
    assert all(s.name == test_name for s in filtered)
    if filtered:
        assert isinstance(filtered[0], Subject)


def test_get_subjects_by_nonexistent_name(client: HiveClient):
    result = list(client.get_subjects(subject_name="__unlikely_to_exist__"))
    assert len(result) == 0


@pytest.mark.parametrize(
    "filter_arg,attr_name",
    [
        ("parent_program__id__in", "parent_program_id"),
        ("parent_program", "parent_program_id"),
    ],
)
def test_get_subjects_by_parent_program(
    client: HiveClient,
    filter_arg: Literal["parent_program__id__in"] | Literal["parent_program"],
    attr_name: Literal["parent_program_id"],
):
    all_programs = list(client.get_programs())
    if not all_programs:
        pytest.skip("No programs available for parent_program tests.")
    program = all_programs[0]
    value = [program.id] if filter_arg.endswith("__in") else program
    filtered = list(
        client.get_subjects(
            **{filter_arg: value}  # pyright: ignore[reportArgumentType]
        )
    )
    assert (
        all(getattr(s, attr_name) == program.id for s in filtered) or len(filtered) == 0
    )


def test_subjects_conflict_parent_program_filters(client: HiveClient):
    all_programs = list(client.get_programs())
    if not all_programs:
        pytest.skip("No programs available for conflict tests.")
    program = all_programs[0]
    with pytest.raises(AssertionError):
        list(
            client.get_subjects(
                parent_program__id__in=[program.id + 123456],
                parent_program=program,
            )
        )


def test_subjects_both_program_filters_match_allowed(client: HiveClient):
    all_programs = list(client.get_programs())
    if not all_programs:
        pytest.skip("No programs available for conflict tests.")
    program = all_programs[0]
    subjects = list(
        client.get_subjects(
            parent_program__id__in=[program.id],
            parent_program=program,
        )
    )
    assert isinstance(subjects, list)


# --- Create Subject Tests ---


@pytest.mark.parametrize(
    "symbol,name,color,segel_brief",
    [
        ("MATH", "Mathematics", "#FF0000", ""),  # Normal case, empty segel_brief
        (
            "SCI",
            "Science",
            "#00FF00",
            "Excellent progress",
        ),  # Normal case with segel_brief
        ("LONG" * 10, "LongSymbol", "#ABCDEF", ""),  # Edge case: very long symbol
        ("PHY", "Physics", "#FFEEAA", "A" * 500),  # Edge case: very long segel_brief
    ],
)
def test_create_subject(
    client: HiveClient,
    program: Program,
    symbol: LiteralString | Literal["MATH"] | Literal["SCI"] | Literal["PHY"],
    name: (
        Literal["Mathematics"]
        | Literal["Science"]
        | Literal["LongSymbol"]
        | Literal["Physics"]
    ),
    color: (
        Literal["#FF0000"]
        | Literal["#00FF00"]
        | Literal["#ABCDEF"]
        | Literal["#FFEEAA"]
    ),
    segel_brief: LiteralString | Literal[""] | Literal["Excellent progress"],
):
    subject = client.create_subject(
        symbol=symbol, name=name, program=program, color=color, segel_brief=segel_brief
    )

    # Ensure a Subject instance is returned
    assert isinstance(subject, Subject)
    assert subject.name == name
    assert subject.symbol == symbol
    assert subject.color == color
    assert subject.parent_program_id == program.id
    assert subject.segel_brief == segel_brief

    # Cleanup
    client.delete_subject(subject)


def test_create_subject_invalid_program(client: HiveClient):
    """Passing invalid program object should raise an assertion or HTTP error."""
    with pytest.raises((AssertionError, TypeError)):
        client.create_subject(
            "MATH",
            "Math",
            program=None,  # pyright: ignore[reportArgumentType]
            color="#FFFFFF",
        )


# --- Delete Subject Tests ---


def test_delete_subject(client: HiveClient, program: Program):
    subject = client.create_subject("DEL", "ToDelete", program, "#123456")

    # Delete using the client method
    client.delete_subject(subject)

    # Ensure subject no longer exists
    subjects = list(client.get_subjects(subject_name="ToDelete"))
    assert all(s.id != subject.id for s in subjects)


def test_delete_subject_invalid_input(client: HiveClient):
    """Deleting a non-existent subject or invalid input should raise an error."""
    with pytest.raises(Exception):
        client.delete_subject(999999)  # Likely 404
    with pytest.raises(AssertionError):
        client.delete_subject(None)  # pyright: ignore[reportArgumentType]
    with pytest.raises(TypeError):
        client.delete_subject(
            "invalid_type"  # pyright: ignore[reportArgumentType]
        )  #  # Not a Subject or ID


def test_delete_subject_twice(client: HiveClient, program: Program):
    """Deleting a subject twice should fail the second time gracefully."""
    subject = client.create_subject("TWICE", "DeleteTwice", program, "#456456")
    client.delete_subject(subject)
    with pytest.raises(Exception):
        client.delete_subject(subject)  # Second deletion should fail
