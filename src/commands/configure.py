import typer

from rich.prompt import Confirm
from nornir_netmiko.tasks import netmiko_save_config

import tasks.configure

from classes.config import Config
from utils.data_fields import validate_reload_date

CONFIG = Config()


def enable_scp():
    CONFIG.nornir.run(task=tasks.configure.enable_scp_server)


def enable_ssh_bulk_mode():
    CONFIG.nornir.run(task=tasks.configure.enable_ssh_bulk_mode)


def disable_scp():
    CONFIG.nornir.run(task=tasks.configure.disable_scp_server)


def disable_ssh_bulk_mode():
    CONFIG.nornir.run(task=tasks.configure.disable_ssh_bulk_mode)


def set_isr_boot_statement():
    CONFIG.nornir.run(task=tasks.configure.set_router_boot_statement)


def set_switch_boot_statement(
    force: bool = typer.Option(False, is_flag=True, help="Force set boot statement"),
):
    """Set the boot statement for switches
    supports 2960, 3560, 9200, 9300 and 9500 series switches
    """
    CONFIG.nornir.run(task=tasks.configure.set_switch_boot_statement, force=force)


def set_reload(
    time: str, force: bool = typer.Option(False, is_flag=True, help="Force reload")
):
    if not validate_reload_date(time):
        return

    CONFIG.nornir.run(task=tasks.configure.set_reload, reload_time=time, force=force)


def ensure_ntp(
    vlan: int | None = typer.Option(None, help="Vlan ID for NTP"),
    ntp_servers: str | None = typer.Option(
        None, help="Comma Separated list of NTP servers. Ex: 172.16.1.2,172.16.1.3"
    ),
):
    """Ensure NTP is configured on all devices"""

    if vlan is None and (vlan := CONFIG.env.ntp_vlan) is None:
        raise ValueError("NTP VLAN not specified")

    if ntp_servers is None:
        if (servers := CONFIG.env.ntp_servers) is None:
            raise ValueError("NTP servers not specified")
    else:
        servers = ntp_servers.split(",")

    commands = [
        f"ntp source Vlan{vlan}",
    ]

    for server in servers:
        commands.append(f"ntp server {server}")

    CONFIG.nornir.run(task=tasks.configure.check_and_set_ntp, commands=commands)


def reload():
    if Confirm.ask("Are you sure you want to reload the devices?"):
        CONFIG.nornir.run(task=tasks.configure.reload)


def cancel_reload_at_target():
    CONFIG.nornir.run(task=tasks.configure.cancel_reload_at_target)


def save_config():
    try:
        CONFIG.nornir.run(task=netmiko_save_config)
    except Exception as e:
        print(f"Error saving configuration: {e}")
