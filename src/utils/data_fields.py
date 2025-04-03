from typing import Any

import logging
import re

from nornir.core.inventory import Host


class StackInfoFields:
    IS_STACK = "is_stack"
    MEMBERS = "stack_members"
    MASTER = "stack_master"
    TARGET_IN_FLASH = "target_in_flash"


class DataFields:
    PRIMARY_IMAGE = "primary_image"
    PRIMARY_IMAGE_SIZE = "primary_image_size"
    PRIMARY_IMAGE_MD5 = "primary_image_md5"
    PRIMARY_IMAGE_MD5_VERIFIED = "primary_image_md5_verified"
    PRIMARY_IMAGE_IN_FLASH = "primary_image_in_flash"
    FLASH_SPACE_AVAILABLE = "flash_space_available"
    CURRENT_IMAGE = "current_image"
    IS_AT_TARGET = "is_at_target"
    IOS_VERSION = "ios_version"
    IMAGES_TO_DELETE = "images_to_delete"
    STACK_INFO = "stack_info"
    PLATFORM = "platform"
    SCP_ENABLED = "scp_enabled"
    SSH_BULK_MODE = "ssh_bulk_mode"
    SUPPORTS_SSH_BULK_MODE = "supports_ssh_bulk_mode"
    RELOAD_TIME = "reload_time"
    RELOAD_SET = "reload_set"
    BOOT_STATEMENT_SET = "boot_statement_set"
    DNS_IP = "dns_ip"
    HOSTNAME_VERIFIED = "hostname_verified"
    SOLARWINDS_STATUS = "solarwinds_status"
    PING_STATUS = "ping_status"
    INACTIVE = "inactive"
    AUTH_STATUS = "auth_status"
    CONNECTION_ERROR = "connection_error"


def check_host_has_valid_stack_info(
    hostname: str | Host, stack_info: dict[str, Any]
) -> bool:
    """Check that all values are present in the dictionary"""

    if stack_info is None:
        logging.error("stack_info not found for %s", hostname)
        return False

    is_stack = stack_info.get(StackInfoFields.IS_STACK, None)

    if is_stack is False:
        return True

    missing = []
    if is_stack is None:
        missing.append(StackInfoFields.IS_STACK)

    if stack_info.get(StackInfoFields.MEMBERS) is None:
        missing.append(StackInfoFields.MEMBERS)

    if stack_info.get(StackInfoFields.MASTER) is None:
        missing.append(StackInfoFields.MASTER)

    if missing:
        logging.error("%s in stack_info not found for %s", ", ".join(missing), hostname)
        return False

    return True


def get_required_host_vars(host: Host, required_vars: list[str]) -> list[Any]:
    """Check that all required variables are present in the task.host"""
    success = True
    return_list = []
    missing = []
    for var in required_vars:
        if var == DataFields.STACK_INFO:
            stack_info = host.get(var)
            return_list.append(stack_info)
            if not check_host_has_valid_stack_info(host, stack_info):
                success = False
            continue

        value = host.get(var)
        return_list.append(value)
        if value is None:
            missing.append(var)
            success = False

    if missing:
        logging.error("%s not found for %s", ", ".join(missing), host)

    return_list.insert(0, success)
    return return_list


def validate_reload_date(reload_date: str) -> bool:
    """Validate that the reload time is in the correct format"""
    reload_date = reload_date.strip().lower()
    reload_regex = re.compile(
        r"^(?P<hour>[01]\d|2[0-3]):(?P<minutes>[0-5]\d)\s(?P<day>[0-2]\d|3[01])\s(?P<month>jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)$"
    )

    match = reload_regex.match(reload_date)

    if match:
        if day := match.group("day"):
            day = int(day)
            month = match.group("month")
            if not month:
                logging.error(
                    "Invalid reload command."
                    "Please specify month with 3 letter month abbreviation."
                )
                return False
            if day > 31:
                logging.error("Invalid reload command. %s exceeded days in month", day)
                return False
            if month in ["apr", "jun", "sep", "nov"] and day > 30:
                logging.error("Invalid reload command. %s exceeded days in month", day)
                return False
            elif month == "feb" and day > 29:
                logging.error("Invalid reload command. %s exceeded days in month", day)
                return False

        return True
    else:
        logging.error("Invalid reload command. Format should be HH:MM DD MMM")
        return False
