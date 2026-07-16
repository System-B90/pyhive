"""
Name: state.py
Purpose: Maintains global state for PyHive CLI execution, including authentication credentials.
Created: 2026-04-07
Author: Michael K. Steinberg
"""


class CLIState:  # pylint: disable=too-few-public-methods
    """
    Global state container for the CLI.

    Args:
        None

    Returns:
        None
    """

    def __init__(self) -> None:
        """
        Initialize the CLI state.

        Args:
            None

        Returns:
            None
        """
        self.use_json: bool = False
        self.username: str | None = None
        self.password: str | None = None
        self.access_token: str | None = None
        self.cache_token: bool = False


state = CLIState()
