import logging

from nornir.core.task import Task
from nornir_netmiko.tasks import (
    netmiko_send_command,
    netmiko_send_config,
    netmiko_save_config,
)

from tasks.verify import verify_boot_statement, verify_switch_boot_statement
from utils.data_fields import DataFields, get_required_host_vars, StackInfoFields


def enable_ssh_bulk_mode(task: Task):
    """Turns on SSH bulk mode on remote hosts"""
    if task.host.data.get(DataFields.SUPPORTS_SSH_BULK_MODE) is False:
        logging.info("SKIPPING SSH bulk mode on %s: Not supported", task.host)
        return

    try:
        task.run(
            netmiko_send_config,
            delay_factor=15,
            config_commands=["ip ssh bulk-mode"],
        )
        task.host.data[DataFields.SSH_BULK_MODE] = True
    except Exception:
        logging.warning("Error enabling SSH bulk mode on %s: %s", task.host)


def disable_ssh_bulk_mode(task: Task):
    """Turns off SSH bulk mode on remote hosts"""
    if task.host.data.get(DataFields.SUPPORTS_SSH_BULK_MODE) is False:
        return

    try:
        task.run(
            netmiko_send_config,
            delay_factor=15,
            config_commands=["no ip ssh bulk-mode"],
        )
        task.host.data[DataFields.SSH_BULK_MODE] = False
    except Exception:
        logging.warning("Error disabling SSH bulk mode on %s: %s", task.host)


def enable_scp_server(
    task: Task,
    commands: list[str] = [
        "line vty 0 4",
        "exec-timeout 360 0",
        "ip scp server enable",
    ],
):
    """Turns on SCP server on remote hosts, increases exec timeout time"""
    try:
        task.run(
            netmiko_send_config,
            delay_factor=15,
            config_commands=commands,
        )
        task.host.data[DataFields.SCP_ENABLED] = True
    except Exception as e:
        logging.error("Error enabling SCP server on %s: %s", task.host, e)


def disable_scp_server(
    task: Task,
    commands: list[str] = [
        "line vty 0 4",
        "exec-timeout 30 0",
        "no ip scp server enable",
    ],
):
    """Turns SCP server off on remote hosts, turns timeout time back to 30 minutes"""
    task.run(
        netmiko_send_config,
        delay_factor=15,
        config_commands=commands,
    )
    task.host.data[DataFields.SCP_ENABLED] = False


def set_switch_boot_statement(task: Task, force: bool = True):
    success, primary_image, current_image, stack_info = get_required_host_vars(
        task.host,
        [DataFields.PRIMARY_IMAGE, DataFields.CURRENT_IMAGE, DataFields.STACK_INFO],
    )

    if not success:
        return

    if not force and task.host.data.get(DataFields.BOOT_STATEMENT_SET):
        logging.info("SKIPPING boot statement on %s: Already set", task.host)
        return

    flash = f"flash:{primary_image}{f';flash:{current_image}' if current_image else ''}"
    commands = ["no boot system", f"boot system {flash}"]

    if stack_info[StackInfoFields.IS_STACK]:
        commands = ["no boot system switch all", f"boot system switch all {flash}"]

    logging.info("Setting boot statement on %s: %s", task.host, commands)

    task.run(
        netmiko_send_config, delay_factor=30, config_commands=commands, enable=True
    )

    try:
        task.run(task=netmiko_save_config)
    except Exception as e:
        logging.error("Error copying run to start on %s: %s", task.host, e)
        return

    boot_var_success = verify_switch_boot_statement(task)

    if boot_var_success is False:
        logging.error("Boot statement not set on %s: %s", task.host, commands)
        return

    task.host.data[DataFields.BOOT_STATEMENT_SET] = True


def set_router_boot_statement(task: Task):
    success, primary_image, current_image = get_required_host_vars(
        task.host,
        [DataFields.PRIMARY_IMAGE, DataFields.CURRENT_IMAGE],
    )

    if not success:
        return

    if task.host.data.get(DataFields.BOOT_STATEMENT_SET):
        logging.info("SKIPPING boot statement on %s: Already set", task.host)
        return

    flash = f"flash:{primary_image}{f';flash:{current_image}' if current_image else ''}"
    commands = [
        "no boot system",
        f"boot system bootflash:{primary_image}",
        f"boot system bootflash:{current_image}",
    ]

    logging.info("Setting boot statement on %s: %s", task.host, commands)

    task.run(
        netmiko_send_config, delay_factor=15, config_commands=commands, enable=True
    )
    try:
        task.run(task=netmiko_save_config)
    except Exception as e:
        logging.error("Error copying run to start on %s: %s", task.host, e)
        return

    boot_var_success = verify_boot_statement(task)

    if boot_var_success is False:
        logging.error("Boot statement not set on %s: %s", task.host, commands)
        return

    task.host.data[DataFields.BOOT_STATEMENT_SET] = True


def set_reload(task: Task, reload_time: str, force: bool = True):
    if not force and task.host.data.get(DataFields.IS_AT_TARGET):
        logging.info("SKIPPING reload on %s: Is at Target", task.host)
        return

    if not reload_time:
        logging.error("no reload_time given")
        return

    if (
        not force
        and task.host.data.get(DataFields.RELOAD_TIME) == reload_time
        and task.host.data.get(DataFields.RELOAD_SET)
    ):
        logging.info("SKIPPING reload on %s: Already set at %s", task.host, reload_time)
        return

    commands = f"reload at {reload_time}\nyes\n\nshow reload\n"
    result = task.run(
        task=netmiko_send_command,
        use_timing=True,
        command_string=commands,
    )

    logging.info("Reload set on %s: %s", task.host, result.result)
    task.host.data[DataFields.RELOAD_TIME] = reload_time


def check_and_set_ntp(task: Task, commands: list[str]):
    """Check if NTP is configured and set it if not"""

    command = "show ntp status"
    result = task.run(task=netmiko_send_command, command_string=command)

    if "Clock is synchronized" in result.result:
        return

    task.run(netmiko_send_config, delay_factor=4, config_commands=commands)


def cancel_reload_at_target(task: Task):
    success, is_at_target = get_required_host_vars(task.host, [DataFields.IS_AT_TARGET])

    if not success:
        return

    if not is_at_target:
        logging.info("SKIPPING reload on %s: Is at Target", task.host)
        return

    commands = "reload cancel"
    result = task.run(
        task=netmiko_send_command,
        command_string=commands,
    )

    logging.info(
        "%s - Reload canceled on %s: %s", is_at_target, task.host, result.result
    )


def reload(task: Task):
    success, is_at_target = get_required_host_vars(task.host, [DataFields.IS_AT_TARGET])

    if not success:
        return

    if is_at_target:
        logging.info("SKIPPING reload on %s: Is at Target", task.host)
        return

    commands = "reload\nyes\n\n"
    result = task.run(
        task=netmiko_send_command,
        command_string=commands,
    )

    logging.info("Reload initiated on %s: %s", task.host, result.result)
    task.host.data[DataFields.RELOAD_SET] = True
