import time

import pytest
from httpx import HTTPStatusError

from pyhive.src.types.program import Program


def test_get_programs(client):
    programs = list(client.get_programs())
    assert len(programs) > 0  # ensure we have programs
    for p in programs:
        assert isinstance(p, Program)


def test_get_program_by_id(client):
    programs = list(client.get_programs())
    assert programs, "No programs available for testing"

    first = programs[0]
    looked_up = client.get_program(first.id)

    assert looked_up.id == first.id
    assert looked_up.name == first.name


def test_get_programs_by_name(client):
    programs = list(client.get_programs())
    assert programs, "No programs available for testing"

    name = programs[0].name
    filtered = list(client.get_programs(program_name=name))

    assert filtered
    assert all(p.name == name for p in filtered)
    assert isinstance(filtered[0], Program)


def test_get_programs_by_nonexistent_name(client):
    result = list(client.get_programs(program_name="__unlikely_to_exist__"))
    assert len(result) == 0


@pytest.mark.parametrize("delete_method", ["client", "instance"])
def test_create_and_delete_program(client, delete_method):
    name = f"Dummy Program {int(time.time())}"
    checker = next(iter(client.get_users()))

    # Create
    program = client.create_program(name, checker=checker)

    # Validate created
    assert client.get_program(program.id).name == name
    assert next(client.get_programs(id__in=[program.id])).name == name
    assert next(client.get_programs(program_name=name)).id == program.id
    assert program.checker.id == checker.id

    # Delete using chosen method
    if delete_method == "client":
        client.delete_program(program)
    else:
        program.delete()

    # Expect 404 when fetching deleted program
    with pytest.raises(HTTPStatusError):
        client.get_program(program.id)

    # Ensure no longer listed
    assert not list(client.get_programs(program_name=name))
