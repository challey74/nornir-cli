import inspect
import readline
import shlex
import logging

from enum import Enum
from sys import platform

from rich import print  # pylint: disable=W0622

from cli import app


class ExitCommands(str, Enum):
    EXIT = "exit"
    CTRL_X = "\x18"
    QUIT = "quit"
    Q = "q"
    X = "x"


class Shell:
    def __init__(self, project_name: str = "Nornir"):
        self.project_name = project_name
        self.options: dict[str, list[str] | None] = self._initialize_options()
        self._setup_readline()
        self.logger = logging.getLogger(__name__)

    def _initialize_options(self) -> dict[str, list[str] | None]:
        options = {
            "--help": None,
            "--install-completion": None,
            "--show-completion": None,
        }
        for function in app.registered_commands:
            command_name = function.callback.__name__.replace("_", "-")
            parameters = inspect.signature(function.callback).parameters
            parameter_names = [
                f'--{p.replace("_", "-")}' for p in parameters if p != "self"
            ]
            parameter_names.append("--help")
            options[command_name] = parameter_names
        return options

    def _complete(self, text: str, state: int) -> str | None:
        """Return the state'th completion for text."""
        line = readline.get_line_buffer()
        parts = line.split()

        # at the start or completing a command
        if len(parts) <= 1:
            if text:
                matches = [cmd for cmd in self.options.keys() if cmd.startswith(text)]
            else:
                matches = list(self.options.keys())
        # completing a parameter for a command
        elif parts[0] in self.options and text.startswith("--"):
            command_params = self.options[parts[0]]
            if command_params:  # Check if command has parameters
                matches = [param for param in command_params if param.startswith(text)]
            else:
                matches = []
        else:
            matches = []

        try:
            return matches[state]
        except IndexError:
            return None

    def _setup_readline(self) -> None:
        readline.set_completer(self._complete)
        readline.set_completer_delims(" \t\n;")

        if platform == "darwin":  # macOS
            readline.parse_and_bind("bind ^I rl_complete")
        elif platform == "win32":  # Windows
            try:
                # Try to use pyreadline3 if available
                import pyreadline3

                readline.parse_and_bind("tab: complete")
            except ImportError:
                print(
                    "[yellow]Warning: Install pyreadline3 for better tab completion on Windows"
                )
                readline.parse_and_bind("tab: complete")
        else:  # Linux and others
            readline.parse_and_bind("tab: complete")

    def _parse_input(self, user_input: str) -> list[str] | None:
        """Parse user input handling quoted strings properly using shlex."""
        if not user_input:
            return None
        try:
            return shlex.split(user_input)
        except ValueError as e:
            self.logger.error(f"Input parsing error: {e}")
            print(f"[red bold]Input error: {e}")
            return None

    def _process_command(self, command: str) -> bool:
        """Process a command and return True if should continue, False to exit."""
        if command.strip().lower() in ExitCommands.__members__.values():
            print("[red]Exiting...")
            return False

        try:
            args = self._parse_input(command)
            if args:
                app(args)
        except AssertionError:
            print(f'[red]Invalid command: [/][bright_cyan bold]"{command}"')
        except SystemExit:
            self.logger.debug("SystemExit caught")
        except Exception as e:
            self.logger.exception("Command processing error")
            print(f"[red bold]Error: {str(e)}")
        return True

    def run(self) -> None:
        """Start the interactive shell session."""
        while True:
            try:
                command = input(f"{self.project_name} >>> ")
                if not self._process_command(command):
                    break
            except EOFError:
                print("\n[red]Aborted.")
                break
            except KeyboardInterrupt:
                print("\n[yellow]Operation cancelled.")
                continue


def shell():
    """Start an interactive shell session."""
    Shell().run()
