import logging

from typing import Any, Callable, Sequence

from nornir.core.task import Task
from nornir.core.inventory import Host
from nornir_netmiko.tasks import netmiko_send_command
from nornir_napalm.plugins.tasks import napalm_get

from utils.data_fields import (
    DataField,
    DataFields,
    StackInfoFields,
)


def get_hostname(task: Task) -> str | None:
    result = task.run(task=napalm_get, getters=["get_facts"])
    hostname = result[0].result["get_facts"]["hostname"]
    expected_hostname = (task.host.name).split(".")[0].lower()
    if hostname.lower() != expected_hostname:
        logging.error(
            "%s: Hostname mismatch - Found: %s Expected: %s",
            task.host,
            hostname,
            expected_hostname,
        )

    return hostname


def is_router(host: Host) -> bool:
    """Check if the host is a router based on its hostname."""
    return "cir" in host.name


def get_stack_info(
    task: Task, force: bool = False, filters: Sequence[Callable] | None = [is_router]
):
    """Gets stack information from the device and stores it in the host data.
    If the device is not a stack, it sets the is stack to False
    and stack info fields to None.

    Args:
        task (Task): Nornir task object.
        force (bool, optional): Force the retrieval of stack info. Defaults to False.
        filter (Callable, optional): A callable to filter devices that should not
        be considered stacks. Defaults to None.
    """

    if not force and task.host.get(DataFields.STACK_INFO) is not None:
        return

    stack_info: dict[DataField, Any] = {
        StackInfoFields.IS_STACK: None,
        StackInfoFields.MEMBERS: None,
        StackInfoFields.MASTER: None,
    }

    if filters is not None and any(filter(task.host) for filter in filters):
        stack_info[StackInfoFields.IS_STACK] = False
        task.host.data[DataFields.STACK_INFO] = stack_info
        return

    result = task.run(
        task=netmiko_send_command,
        command_string="show switch",
        use_genie=True,
    )

    output = result.result

    if isinstance(output, str):
        if output.lower().find("invalid input") != -1 or not output.strip():
            stack_info[StackInfoFields.IS_STACK] = False
            task.host.data[DataFields.STACK_INFO] = stack_info
            return

        logging.error("Error getting stack info. Unsupported str output: %s", output)
        return

    logging.debug("%s - %s", task.host, output)

    active_switches = {
        switch_num: switch_data
        for switch_num, switch_data in output["switch"]["stack"].items()
        if switch_data["state"] != "provisioned"
    }

    if len(active_switches) <= 1:
        stack_info[StackInfoFields.IS_STACK] = False
    else:
        stack_info[StackInfoFields.IS_STACK] = True
        stack_info[StackInfoFields.MEMBERS] = list(active_switches.keys())
        for num, data in active_switches.items():
            if data["role"] in ("master", "active"):
                stack_info[StackInfoFields.MASTER] = num
                break

    task.host.data[DataFields.STACK_INFO] = stack_info


def get_ios_version(task: Task):
    result = task.run(task=napalm_get, getters=["get_facts"])
    ios_version = result[0].result["get_facts"]["os_version"]
    for line in ios_version.split(","):
        if "version" in line.lower():
            ios_version = line.split()[1]
            break

    task.host.data[DataFields.IOS_VERSION] = ios_version
    logging.info("%s: %s", task.host, ios_version)


def get_number_of_gb_ports(task: Task):
    result = task.run(task=napalm_get, getters=["get_interfaces"])
    interfaces = result[0].result["get_interfaces"]
    count = 0
    for interface in interfaces.keys():
        if interface.lower().startswith("gigabite"):
            count += 1
    logging.info("%s port count: %s", task.host, count)
    task.host.data["number_of_interfaces"] = count


def get_current_image(task: Task, force: bool = True):
    if not force and task.host.get(DataFields.CURRENT_IMAGE) is not None:
        return

    result = task.run(
        task=netmiko_send_command, command_string="show version | include image"
    )

    system_image = str(result[0]).strip().split()[-1]
    image_name = system_image.strip('"')
    possible_image_prefix = ["flash", "bootflash", "bootvar"]
    for prefix in possible_image_prefix:
        if prefix in image_name:
            image_name = image_name.split(":")[-1]
            break

    task.host.data[DataFields.CURRENT_IMAGE] = image_name

    primary_image = task.host.get(DataFields.PRIMARY_IMAGE)
    is_at_target = primary_image and primary_image == image_name
    task.host.data[DataFields.IS_AT_TARGET] = is_at_target

    logging.info(
        "%s system image: %s\nIs at Target: %s", task.host, image_name, is_at_target
    )
