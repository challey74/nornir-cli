"""Main entry point"""

import typer

from commands.inventory.get_inventory import _user_select_get_inventory
from utils.import_commands import import_commands
from classes.config import Config

app = import_commands(typer.Typer())

CONFIG = Config()
CONFIG.nornir_loader = _user_select_get_inventory


if __name__ == "__main__":
    app()
