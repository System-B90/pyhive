"""
Name: test_cli_formatter.py
Purpose: Unit tests for pyhive/cli/formatter.py — print_result, print_error_and_exit,
    print_formatted_list, print_info.
"""

import json

import pytest
import typer

from pyhive.cli import formatter
from pyhive.cli.state import CLIState


@pytest.fixture(autouse=True)
def fresh_state(monkeypatch):
    fresh = CLIState()
    monkeypatch.setattr(formatter, "state", fresh)
    return fresh


def test_print_result_json_mode_dumps_json(capsys, fresh_state):
    fresh_state.use_json = True

    formatter.print_result(
        {"a": 1}, lambda: (_ for _ in ()).throw(AssertionError("should not run"))
    )

    out = capsys.readouterr().out
    assert json.loads(out) == {"a": 1}


def test_print_result_text_mode_calls_fallback(capsys, fresh_state):
    fresh_state.use_json = False
    called = {"ran": False}

    def fallback() -> None:
        called["ran"] = True
        typer.echo("text!")

    formatter.print_result({"a": 1}, fallback)

    assert called["ran"] is True
    assert "text!" in capsys.readouterr().out


def test_print_error_and_exit_json_mode(capsys, fresh_state):
    fresh_state.use_json = True

    with pytest.raises(typer.Exit) as exc:
        formatter.print_error_and_exit("boom", {"error": "boom", "code": 7})

    assert exc.value.exit_code == 1
    err = capsys.readouterr().err
    assert json.loads(err) == {"error": "boom", "code": 7}


def test_print_error_and_exit_json_mode_defaults_error_data(capsys, fresh_state):
    fresh_state.use_json = True

    with pytest.raises(typer.Exit) as exc:
        formatter.print_error_and_exit("boom")

    assert exc.value.exit_code == 1
    err = capsys.readouterr().err
    assert json.loads(err) == {"error": "boom"}


def test_print_error_and_exit_text_mode(capsys, fresh_state):
    fresh_state.use_json = False

    with pytest.raises(typer.Exit) as exc:
        formatter.print_error_and_exit("boom")

    assert exc.value.exit_code == 1
    err = capsys.readouterr().err
    assert "Error: boom" in err


def test_print_formatted_list_empty_returns_early(capsys):
    formatter.print_formatted_list([], "- {id}", ["id"])

    assert capsys.readouterr().out == ""


def test_print_formatted_list_column_alignment():
    from typer.testing import CliRunner

    app = typer.Typer()

    @app.command()
    def cmd() -> None:
        formatter.print_formatted_list(
            [{"id": 1, "name": "a"}, {"id": 22, "name": "bb"}],
            "[{id}] {name}",
            ["id", "name"],
        )

    result = CliRunner().invoke(app, [])
    lines = [line for line in result.output.splitlines() if line]
    assert lines[0] == "[ 1]  a"
    assert lines[1] == "[22] bb"


def test_print_info_suppressed_in_json_mode(capsys, fresh_state):
    fresh_state.use_json = True
    formatter.print_info("hello")
    assert capsys.readouterr().out == ""


def test_print_info_shown_in_text_mode(capsys, fresh_state):
    fresh_state.use_json = False
    formatter.print_info("hello")
    assert "hello" in capsys.readouterr().out
