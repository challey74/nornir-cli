import logging

from nornir.core.task import Task
from nornir_netmiko.tasks import netmiko_send_command, netmiko_send_config

from classes.config import Config

CONFIG = Config()

COMMAND = "show run | include clock"


def get_timezone(task: Task, command: str = COMMAND):
    result = task.run(task=netmiko_send_command, command_string=command)
    logging.info(task.host, result.result)


def check_and_set_timezone(
    task: Task, timezone: str = CONFIG.env.timezone, command: str = COMMAND
):
    result = task.run(task=netmiko_send_command, command_string=command)

    logging.info(task.host, result.result)

    timezone_command = f"clock timezone {timezone}"

    if not result.result:
        logging.error("Unable to get clock info for %s", task.host)
        return

    if timezone.lower() not in result.result.lower():
        commands = [timezone_command]
        task.run(netmiko_send_config, config_commands=commands)
        logging.info("Timezone set on %s", task.host)
