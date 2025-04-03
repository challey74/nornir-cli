import typer

import tasks.verify

from classes.config import Config

CONFIG = Config()


def verify_switch_boot_statement(
    target_check_only: bool = typer.Option(
        False, is_flag=True, help="Allows to not have current image data"
    ),
):
    """Verify boot statement on 2960, 3560, 9200 and 9300 switches"""

    CONFIG.nornir.run(
        task=tasks.verify.verify_switch_boot_statement,
        target_check_only=target_check_only,
    )


def verify_isr_boot_statement():
    """Verify boot statement on all devices"""

    CONFIG.nornir.run(task=tasks.verify.verify_boot_statement)


def verify_md5(
    force: bool = typer.Option(False, is_flag=True, help="Force MD5 verification"),
):
    CONFIG.nornir.run(task=tasks.verify.verify_md5, force=force)


def verify_reload(
    force: bool = typer.Option(False, is_flag=True, help="Force reload verification"),
):
    CONFIG.nornir.run(task=tasks.verify.verify_reload, force=force)


def check_no_reload():
    CONFIG.nornir.run(task=tasks.verify.check_no_reload)
