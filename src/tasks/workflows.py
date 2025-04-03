import json
import logging
import socket
import os

from datetime import datetime

from nornir.core.task import Task

import tasks.configure
import tasks.connectivity
import tasks.device_info
import tasks.flash
import tasks.nornir
import tasks.solarwinds
import tasks.support
import tasks.transfer
import tasks.verify

from utils.data_fields import DataFields
from utils.helpers import clean_hostname
from classes.config import Config

CONFIG = Config()


def check_and_handle_tacacs_credentials():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    inventory = CONFIG.nornir.inventory
    CONFIG.nornir.run(task=tasks.connectivity.check_credentials)

    failed_hosts = [
        host.name
        for host in inventory.hosts.values()
        if not host.data.get(DataFields.AUTH_STATUS)
    ]

    if not failed_hosts:
        logging.info("All hosts successfully authenticated")
        return

    with open(
        os.path.join(
            CONFIG.reports_folder,
            f"v2_failed_auth_{CONFIG.metadata.name}_{timestamp}.json",
        ),
        "w",
    ) as f:
        json.dump(failed_hosts, f, indent=2)

    failed_nr = CONFIG.nornir.filter(filter_func=lambda h: h.name in failed_hosts)

    for host in failed_nr.inventory.hosts.values():
        host.password = CONFIG.env.tacacs_v1_password
        host.username = CONFIG.env.tacacs_v1_username

    failed_nr.run(task=tasks.connectivity.check_credentials)

    still_failed = [
        host.name
        for host in failed_nr.inventory.hosts.values()
        if not host.data.get(DataFields.AUTH_STATUS)
    ]

    if not still_failed:
        logging.info("All hosts successfully authenticated with v1 password")
        return

    with open(
        os.path.join(
            CONFIG.reports_folder,
            f"v1_still_failed_auth_{CONFIG.metadata.name}_{timestamp}.json",
        ),
        "w",
    ) as f:
        json.dump(still_failed, f, indent=2)

    logging.warning(
        "%s hosts still failed to authenticate with v1 password", len(still_failed)
    )


def check_status():
    inventory = CONFIG.nornir.inventory
    inactive_hosts = {}
    sw_up_ping_failed = {}
    sw_down_ping_successful = {}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    hosts = [clean_hostname(host.name) for host in inventory.hosts.values()]
    statuses = tasks.solarwinds.get_devices_status(hosts)

    CONFIG.nornir.run(task=tasks.connectivity.check_ping)

    for host in inventory.hosts.values():
        solarwinds_status = statuses.get(clean_hostname(host.name), False)
        host.data[DataFields.SOLARWINDS_STATUS] = solarwinds_status

        host.data[DataFields.INACTIVE] = False

        ping_status = host.data.get(DataFields.PING_STATUS)

        if not solarwinds_status:
            message = f"{host.name}: Status Down in SolarWinds"

            if not ping_status:
                message += ", Ping Failed. Marking as Inactive"
                host.data[DataFields.INACTIVE] = True
                inactive_hosts[host.name] = "Down in SW and ping failed"
            else:
                message += ", Ping Successful"
                sw_down_ping_successful[host.name] = "Down in SW but ping successful"

            logging.warning(message)
            continue

        if not ping_status:
            message = f"{host.name}: Ping Failed, but Status Up in SolarWinds"
            logging.error(message)
            sw_up_ping_failed[host.name] = "Up in SW but ping failed"

    if inactive_hosts:
        inactive_path = os.path.join(
            CONFIG.reports_folder,
            f"inactive_hosts_{CONFIG.metadata.name}_{timestamp}.json",
        )
        with open(inactive_path, "w") as f:
            json.dump(inactive_hosts, f, indent=2)
        logging.warning(
            "%s Inactive hosts found. Check %s", len(inactive_hosts), inactive_path
        )

    if sw_up_ping_failed:
        ping_failed_path = os.path.join(
            CONFIG.reports_folder,
            f"sw_up_ping_failed_{CONFIG.metadata.name}_{timestamp}.json",
        )
        with open(ping_failed_path, "w") as f:
            json.dump(sw_up_ping_failed, f, indent=2)
        logging.warning(
            "%s hosts with failed ping found. Check %s",
            len(sw_up_ping_failed),
            ping_failed_path,
        )

    if sw_down_ping_successful:
        sw_down_ping_successful_path = os.path.join(
            CONFIG.reports_folder,
            f"sw_down_ping_successful_{CONFIG.metadata.name}_{timestamp}.json",
        )
        with open(sw_down_ping_successful_path, "w") as f:
            json.dump(sw_down_ping_successful, f, indent=2)
        logging.warning(
            "%s hosts with failed ping found. Check %s",
            len(sw_down_ping_successful),
            sw_down_ping_successful_path,
        )

    return len(inactive_hosts) == 0


def has_completed_transfer(task: Task):
    if task.host.data.get(DataFields.PRIMARY_IMAGE_IN_FLASH):
        message = f"{task.host.name}: Primary image is in flash and verified. Does not check for stack"
        if task.host.data.get(DataFields.PRIMARY_IMAGE_MD5_VERIFIED):
            logging.info(message)
            return True
        else:
            if task.run(task=tasks.verify.verify_md5) is None:
                return

            if task.host.data.get(DataFields.PRIMARY_IMAGE_MD5_VERIFIED):
                logging.info(message)
                return True

    return False


def _resolve_dns(task: Task) -> str | None:
    try:
        if ip := socket.gethostbyname(task.host.name.split(":")[0]):
            task.host.data[DataFields.DNS_IP] = ip
            return ip
    except socket.gaierror as e:
        logging.error(
            "%s: DNS resolution failed\n%s",
            task.host.name,
            e,
        )
        return None

    task.host.data[DataFields.DNS_IP] = None
    return None


def is_correct_hostname(task: Task) -> bool:
    if task.host.data.get(DataFields.HOSTNAME_VERIFIED):
        return True

    task.host.data[DataFields.HOSTNAME_VERIFIED] = False
    if (ip := task.host.data.get(DataFields.DNS_IP)) is None:
        if (ip := _resolve_dns(task)) is None:
            if (
                hostname := task.run(task=tasks.device_info.get_hostname).result
            ) is None:
                return False

            name = task.host.name.split(":")[0].replace(".telcom.arizona.edu", "")
            if hostname != name:
                logging.error(
                    "Hostname Mismatch\nExpected: %s\nActual: %s",
                    name,
                    hostname,
                )
                return False

    if (
        task.host.hostname != task.host.name and ip != task.host.hostname
    ):  # task.host.hostname is the IP address, name and hostname are device name when missing ip
        logging.error(
            "%s: Inventory and DNS IP mismatch\nInventory: %s\nDNS: %s",
            task.host.name,
            task.host.hostname,
            ip,
        )
        return False

    task.host.data[DataFields.HOSTNAME_VERIFIED] = True
    return True


def _is_at_target(task: Task) -> bool:
    if task.host.data.get(DataFields.IS_AT_TARGET):
        logging.info(f"{task.host.name}: Already at target. Skipping")
        return True

    return False


def transfer_and_verify_image(task: Task, skip_dns_check: bool = False):
    try:
        if not task.host.data.get(DataFields.AUTH_STATUS):
            logging.error(f"{task.host.name}: Authentication failed. Skipping")
            return

        if (
            _is_at_target(task)
            or has_completed_transfer(task)
            or (not skip_dns_check and not is_correct_hostname(task))
        ):
            return

        task.run(task=tasks.device_info.get_stack_info, force=False)
        task.run(task=tasks.device_info.get_current_image, force=False)

        if _is_at_target(task):
            return

        task.run(task=tasks.flash.is_primary_image_in_flash, force=False)

        if has_completed_transfer(task):
            return

        # Delete unused images
        task.run(task=tasks.device_info.get_ios_version)
        task.run(task=tasks.flash.get_images_to_delete)
        task.run(task=tasks.flash.delete_unused_images)

        # Transfer image
        task.run(task=tasks.configure.enable_scp_server)
        task.run(task=tasks.support.supports_ssh_bulk_mode)
        task.run(task=tasks.configure.enable_ssh_bulk_mode)
        task.run(task=tasks.transfer.transfer_image)
        task.run(task=tasks.flash.copy_image_to_stack)
        task.run(task=tasks.configure.disable_scp_server)
        task.run(task=tasks.configure.disable_ssh_bulk_mode)

        # Verify MD5 checksum
        task.run(task=tasks.verify.verify_md5)

    finally:
        task.host.close_connections()
