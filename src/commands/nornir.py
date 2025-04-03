import tasks.nornir

from classes.config import Config
from utils.helpers import add_domain_if_missing

CONFIG = Config()


def edit_md5():
    tasks.nornir.edit_primary_image_md5()


def set_primary_image():
    """Set the primary image for each device type."""
    tasks.nornir.get_primary_image_data()


def remove_hosts(hosts: str):
    """Remove hosts from the inventory."""
    new_hosts = []
    for host in hosts.split(","):
        new_hosts.append(add_domain_if_missing(host.strip()))

    tasks.nornir.remove_hosts(new_hosts)


def select_single_host(host: str):
    tasks.nornir.select_single_host(host)


def print_single_field(field: str):
    CONFIG.nornir.run(task=tasks.nornir.print_single_field, field=field)


def set_single_field(field: str, value: str):
    CONFIG.nornir.run(task=tasks.nornir.set_single_field, field=field, value=value)
