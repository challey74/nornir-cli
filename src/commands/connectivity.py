import tasks.connectivity

from classes.config import Config

CONFIG = Config()


def check_credentials():
    """Check credentials for all devices"""
    CONFIG.nornir.run(tasks.connectivity.check_credentials)


def kill_line_sessions():
    """Kill all line sessions except the current one"""

    CONFIG.nornir.run(tasks.connectivity.kill_line_sessions)
