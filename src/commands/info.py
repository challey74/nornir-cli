from classes.config import Config

import tasks.timezone

CONFIG = Config()


def check_and_set_timezone():
    """Check and set the timezone on a device."""
    CONFIG.nornir.run(task=tasks.timezone.check_and_set_timezone)


def get_timezone():
    """Get the timezone on a device."""
    CONFIG.nornir.run(task=tasks.timezone.get_timezone)
