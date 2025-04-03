"""Import commands into typer from modules in commands folder and subfolders"""

import glob
import importlib
import inspect
import os

import typer

import commands


def import_commands(app: typer.Typer) -> typer.Typer:
    """Import all defined functions from modules in the commands folder.
    Functions imported from other modules or those that start with "_" are not imported.
    Subfolders are imported as well.
    The name of the subfolder is used as the help panel name.
    """

    def add_commands(path: str, subfolder: str | None = None):
        """Add commands from a path. If a subfolder is provided,
        it is used as the help panel name."""

        for module_path in glob.glob(os.path.join(path, "*.py")):
            module_list = ["commands", subfolder, os.path.basename(module_path)[:-3]]
            module = importlib.import_module(
                ".".join([item for item in module_list if item])
            )

            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isfunction(obj)
                    and obj.__module__.startswith("commands.")
                    and not name.startswith("_")
                ):
                    if subfolder:
                        app.command(
                            rich_help_panel=subfolder.title().replace("_", " ")
                        )(obj)
                    else:
                        app.command()(obj)

    path = None
    try:
        commands_path = commands.__path__[0]
        add_commands(commands_path)

        folders = [
            item
            for item in os.listdir(commands_path)
            if os.path.isdir(os.path.join(commands_path, item))
            and not item.startswith("_")
        ]

        for folder in folders:
            path = os.path.join(commands_path, folder)
            add_commands(path=path, subfolder=folder)

    except Exception as e:
        raise Exception(f"Unable to load commands from {path}. {e}") from e

    return app
