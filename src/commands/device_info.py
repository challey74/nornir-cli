import typer

import tasks.device_info

from classes.config import Config

CONFIG = Config()


def get_hostname():
    CONFIG.nornir.run(task=tasks.device_info.get_hostname)


def get_current_image(
    force: bool = typer.Option(
        False, is_flag=True, help="Force the task to run on all devices"
    ),
):
    CONFIG.nornir.run(task=tasks.device_info.get_current_image, force=force)


def get_stack_info(
    force: bool = typer.Option(
        False,
        is_flag=True,
        help="Force the task to run on all devices regardless of stack status",
    ),
):
    CONFIG.nornir.run(task=tasks.device_info.get_stack_info, force=force)


def get_ios_version():
    CONFIG.nornir.run(task=tasks.device_info.get_ios_version)
