"""
Name: test_cli_base.py
Purpose: Unit tests for PyHiveTyper._inject_global_options — global --json /
    --cache-token flag injection at root and nested-subcommand level.
"""

import typer
from typer.testing import CliRunner

from pyhive.cli.base import PyHiveTyper
from pyhive.cli.state import CLIState

runner = CliRunner()


def _fresh_app(monkeypatch, module):
    fresh = CLIState()
    monkeypatch.setattr(module, "state", fresh)
    return fresh


def test_root_level_json_flag_updates_state_before_body(monkeypatch):
    import pyhive.cli.base as base_module

    state = _fresh_app(monkeypatch, base_module)

    app = PyHiveTyper()
    seen: dict[str, bool] = {}

    @app.command()
    def cmd() -> None:
        seen["use_json"] = state.use_json

    result = runner.invoke(app, ["--json"])

    assert result.exit_code == 0
    assert seen["use_json"] is True
    assert state.use_json is True


def test_cache_token_flag_updates_state(monkeypatch):
    import pyhive.cli.base as base_module

    state = _fresh_app(monkeypatch, base_module)

    app = PyHiveTyper()

    @app.command()
    def cmd() -> None:
        pass

    result = runner.invoke(app, ["--cache-token"])

    assert result.exit_code == 0
    assert state.cache_token is True


def test_flag_propagates_through_nested_sub_app(monkeypatch):
    import pyhive.cli.base as base_module

    state = _fresh_app(monkeypatch, base_module)

    sub_app = PyHiveTyper()
    seen: dict[str, bool] = {}

    @sub_app.command(name="list")
    def list_cmd() -> None:
        seen["use_json"] = state.use_json

    root = PyHiveTyper()
    root.add_typer(sub_app, name="items")

    result = runner.invoke(root, ["items", "list", "--json"])

    assert result.exit_code == 0
    assert seen["use_json"] is True


def test_default_false_does_not_clobber_state_set_elsewhere(monkeypatch):
    import pyhive.cli.base as base_module

    state = _fresh_app(monkeypatch, base_module)
    state.use_json = True

    app = PyHiveTyper()
    seen: dict[str, bool] = {}

    @app.command()
    def cmd() -> None:
        seen["use_json"] = state.use_json

    # No --json passed: kwargs.get("use_json") is False, so state.use_json is
    # only ever *set* to True, never reset to False.
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert seen["use_json"] is True


def test_injected_kwargs_are_stripped_from_forwarded_call(monkeypatch):
    import pyhive.cli.base as base_module

    _fresh_app(monkeypatch, base_module)

    app = PyHiveTyper()
    received: dict[str, object] = {}

    @app.command()
    def cmd(name: str = typer.Option("x")) -> None:
        received["kwargs"] = {"name": name}

    result = runner.invoke(app, ["--name", "hello", "--json"])

    assert result.exit_code == 0
    assert received["kwargs"] == {"name": "hello"}


def test_var_keyword_function_receives_full_kwargs(monkeypatch):
    import pyhive.cli.base as base_module

    _fresh_app(monkeypatch, base_module)

    app = PyHiveTyper()
    received: dict[str, object] = {}

    @app.command(
        context_settings={"ignore_unknown_options": True, "allow_extra_args": True}
    )
    def cmd(ctx: typer.Context) -> None:
        received["params"] = dict(ctx.params)

    result = runner.invoke(app, ["--json"])

    assert result.exit_code == 0
