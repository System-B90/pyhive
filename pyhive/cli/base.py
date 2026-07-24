"""
Name: base.py
Purpose: Enterprise Typer subclass with non-destructive global option injection.
Created: 2026-04-07
Author: Michael K. Steinberg
"""

import functools
import inspect
from collections.abc import Callable
from typing import Any, TypeVar, cast

import typer

from pyhive.cli.state import state

F = TypeVar("F", bound=Callable[..., Any])

# Define options with defaults.
GLOBAL_OPTIONS = {
    "use_json": typer.Option(False, "--json", help="Format output as JSON"),
    "cache_token": typer.Option(
        False,
        "--cache-token",
        help="Cache token in OS Keyring. [red]WARNING: Security risk.[/red]",
    ),
}


class PyHiveTyper(typer.Typer):
    """
    Custom Typer subclass that prevents subcommand defaults from overwriting
    global state flags set at the root level.
    """

    def _inject_global_options(self, f: F, base_decorator: Callable[[F], Any]) -> F:
        """
        Injects global options into the function signature.

        Args:
            f (F): The original command function.
            base_decorator (Callable[[F], Any]): The Typer decorator to apply.

        Returns:
            F: The wrapped and decorated function.
        """
        original_sig = inspect.signature(f)
        original_params: set[str] = set(original_sig.parameters.keys())

        new_params = list(original_sig.parameters.values())
        for name, option in reversed(list(GLOBAL_OPTIONS.items())):
            if name not in original_params:
                new_params.append(
                    inspect.Parameter(
                        name,
                        inspect.Parameter.KEYWORD_ONLY,
                        annotation=bool,
                        default=option,
                    )
                )

        # Typer reads __signature__ to build the command's options. F is a
        # TypeVar bound to Callable, which doesn't declare that dunder, so the
        # assignment is invisible to the type system either way.
        f.__signature__ = original_sig.replace(  # type: ignore[attr-defined]
            parameters=new_params
        )

        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if kwargs.get("use_json"):
                state.use_json = True
            if kwargs.get("cache_token"):
                state.cache_token = True

            filtered_kwargs = {k: v for k, v in kwargs.items() if k in original_params}

            if any(p.kind == p.VAR_KEYWORD for p in original_sig.parameters.values()):
                return f(*args, **kwargs)

            return f(*args, **filtered_kwargs)

        # This tells the type checker that the Typer-decorated wrapper
        # satisfies the signature contract of the original function.
        return cast(F, base_decorator(cast(F, wrapper)))

    def command(self, *args: Any, **kwargs: Any) -> Callable[[F], F]:
        decorator = super().command(*args, **kwargs)
        return lambda f: self._inject_global_options(f, decorator)

    def callback(self, *args: Any, **kwargs: Any) -> Callable[[F], F]:
        decorator = super().callback(*args, **kwargs)
        return lambda f: self._inject_global_options(f, decorator)
