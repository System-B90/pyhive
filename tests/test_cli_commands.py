"""
Name: test_cli_commands.py
Purpose: Unit tests for representative CLI command groups (list / get / delete /
    create), stubbing get_hive_client so no network is touched. Also covers the
    `token` command's keyring-write warning path.
"""

import json
from datetime import UTC, datetime
from typing import Any

import pytest
from typer.testing import CliRunner

import pyhive.cli.cli as cli_module
import pyhive.cli.exercises as exercises_module
import pyhive.cli.users as users_module
from pyhive.cli.state import state

runner = CliRunner()


@pytest.fixture(autouse=True)
def fresh_state():
    # All modules share the one `pyhive.cli.state.state` singleton -- reset
    # its fields in place (rather than swapping in a new CLIState) since the
    # global-option injection in base.py mutates that exact object.
    state.use_json = False
    state.cache_token = False
    state.username = None
    state.password = None
    state.access_token = None
    yield state
    state.use_json = False
    state.cache_token = False
    state.username = None
    state.password = None
    state.access_token = None


class _FakeExercise:
    def __init__(self, id_: int) -> None:
        self.id = id_

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": f"Exercise{self.id}",
            "parent_subject_symbol": "A",
        }


class _Clearance:
    name = "HANICH"


class _FakeUser:
    def __init__(self, id_: int, username: str) -> None:
        self.id = id_
        self.username = username
        self.number = 100 + id_
        self.clearance = _Clearance()

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "username": self.username, "number": self.number}

    def model_dump(self) -> dict[str, Any]:
        return {"id": self.id, "username": self.username, "number": self.number}


class _FakeExerciseClient:
    def get_exercises(self):
        return iter([_FakeExercise(1), _FakeExercise(2)])

    def get_exercise(self, exercise_id: int):
        if exercise_id != 1:
            raise ValueError("not found")
        return _FakeExercise(1)

    def delete_exercise(self, exercise_id: int) -> None:
        del exercise_id


class _FakeUserClient:
    def get_users(self):
        return iter([_FakeUser(1, "alice")])

    def create_user(self, **kwargs: Any) -> _FakeUser:
        return _FakeUser(2, kwargs["username"])

    def delete_user(self, user: int) -> None:
        del user


def test_exercises_list_json(monkeypatch):
    monkeypatch.setattr(
        exercises_module, "get_hive_client", lambda **kw: _FakeExerciseClient()
    )
    result = runner.invoke(cli_module.app, ["exercises", "list", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert [e["id"] for e in payload["exercises"]] == [1, 2]


def test_exercises_list_text(monkeypatch):
    monkeypatch.setattr(
        exercises_module, "get_hive_client", lambda **kw: _FakeExerciseClient()
    )
    result = runner.invoke(cli_module.app, ["exercises", "list"])
    assert result.exit_code == 0
    assert "Found 2 exercises" in result.output


def test_exercises_get_json(monkeypatch):
    monkeypatch.setattr(
        exercises_module, "get_hive_client", lambda **kw: _FakeExerciseClient()
    )
    result = runner.invoke(cli_module.app, ["exercises", "get", "1", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["exercise"]["id"] == 1


def test_exercises_get_error_exits_nonzero_json(monkeypatch):
    monkeypatch.setattr(
        exercises_module, "get_hive_client", lambda **kw: _FakeExerciseClient()
    )
    result = runner.invoke(cli_module.app, ["exercises", "get", "999", "--json"])
    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["error"] == "Exercise get failed"


def test_exercises_delete(monkeypatch):
    monkeypatch.setattr(
        exercises_module, "get_hive_client", lambda **kw: _FakeExerciseClient()
    )
    result = runner.invoke(cli_module.app, ["exercises", "delete", "1", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload == {"deleted_exercise_id": 1, "status": "success"}


def test_users_create(monkeypatch):
    monkeypatch.setattr(users_module, "get_hive_client", lambda **kw: _FakeUserClient())
    result = runner.invoke(
        cli_module.app,
        [
            "users",
            "create",
            "bob",
            "--password",
            "Password1",
            "--clearance",
            "hanich",
            "--gender",
            "male",
            "--json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["user"]["username"] == "bob"
    assert payload["status"] == "created"


def test_users_delete(monkeypatch):
    monkeypatch.setattr(users_module, "get_hive_client", lambda **kw: _FakeUserClient())
    result = runner.invoke(cli_module.app, ["users", "delete", "1", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload == {"deleted_user_id": 1, "status": "success"}


def test_token_command_keyring_write_warning(monkeypatch):
    monkeypatch.setattr(
        cli_module,
        "get_sso_token",
        lambda **kw: ("acc", "ref", datetime(2026, 1, 1, tzinfo=UTC)),
    )

    def _raise(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("keyring locked")

    monkeypatch.setattr(cli_module.keyring, "set_password", _raise)

    result = runner.invoke(cli_module.app, ["--cache-token", "token"])

    assert result.exit_code == 0
    assert "could not cache token" in result.output
