import logging
import re

from nornir.core.task import Task
from nornir_netmiko.tasks import netmiko_send_command
from tasks.shared import stack_flash_format

from utils.data_fields import DataFields, get_required_host_vars, StackInfoFields


BOOT_STATEMENT_PATTERNS = {
    "ios": r"^BOOT path-list.*?:flash.*?:",
    "ios-xe": r"^BOOT variable =\s*.*?flash.*?:",
}


def verify_switch_boot_statement(task: Task, target_check_only: bool = False):
    success, primary_image, platform = get_required_host_vars(
        task.host,
        [DataFields.PRIMARY_IMAGE, DataFields.PLATFORM],
    )

    if not success:
        return

    if (
        not target_check_only
        and (current_image := task.host.get(DataFields.CURRENT_IMAGE)) is None
    ):
        return

    result = task.run(netmiko_send_command, command_string="show boot system")

    if not result:
        logging.error("No boot statement found on %s", task.host)
        return False

    if not (
        re.search(f"flash:{primary_image}", result.result)
        or re.search(f"flash:{primary_image};flash:{current_image}", result.result)
    ):
        logging.error("Boot statement not set on %s: %s", task.host, result.result)
        return False

    logging.info("Boot statement verified on %s: %s", task.host, result.result)

    return True


def verify_boot_statement(task: Task):
    """Sends command to show boot statement as outlined in groups.yaml,
    returns success or failure depending on what switch returns"""

    # TODO: add logic for no backup image
    success, primary_image, current_image, platform = get_required_host_vars(
        task.host,
        [DataFields.PRIMARY_IMAGE, DataFields.CURRENT_IMAGE, DataFields.PLATFORM],
    )

    if not success:
        return

    if not platform.lower() == "ios" and not platform.lower() == "ios-xe":
        logging.error(
            "Platform not supported for verify boot statement for %s", task.host
        )
        return

    result = task.run(netmiko_send_command, command_string="show bootvar")

    patterns = []
    for statement in BOOT_STATEMENT_PATTERNS.values():
        patterns.append(
            re.compile(
                rf"{statement}{re.escape(primary_image)}(?:,.*?;|;)(?:.*?flash:{re.escape(current_image)}(?:,.*?;|;))?"
            )
        )

    for pattern in patterns:
        match = re.search(pattern, result.result)
        if match:
            logging.info(
                """SUCCESS bootvar verified on %s:
                \tResult: %s
                \tTarget: %s""",
                task.host,
                match.group(),
                primary_image,
            )
            return True

    logging.error(
        """FAIL (bootvar): %s failed boot statement check:
        \tReturned String: %s
        \tTarget: %s""",
        task.host,
        result.result,
        primary_image,
    )
    return


def check_md5_result(host, result, md5):
    if result.lower().find("done!") == -1:
        logging.error("FAIL - MD5 verification %s. Output: %s", host, result)
        return False

    if md5 in result:
        logging.info(
            "SUCCESS - MD5 verification %s. Expected: %s. Returned: %s",
            host,
            md5,
            result.split()[-1],
        )
        return True

    logging.error(
        "FAIL - MD5 verification %s. Expected: %s. Returned: %s",
        host,
        md5,
        result.split()[-1],
    )

    return False


def verify_md5(task: Task, force: bool = True):
    if not force and task.host.data.get(DataFields.PRIMARY_IMAGE_MD5_VERIFIED):
        return

    success, primary_image, primary_image_md5, stack_info = get_required_host_vars(
        task.host,
        [DataFields.PRIMARY_IMAGE, DataFields.PRIMARY_IMAGE_MD5, DataFields.STACK_INFO],
    )

    if not success:
        return

    task.host.data[DataFields.PRIMARY_IMAGE_MD5_VERIFIED] = False
    if stack_info[StackInfoFields.IS_STACK]:
        stack_format = stack_flash_format(task)
        stack_results = {}
        for i in stack_info[StackInfoFields.MEMBERS]:
            flash = stack_format.format(num=i)
            command = f"verify /md5 {flash}:{primary_image}"

            result = task.run(
                task=netmiko_send_command,
                command_string=command,
                use_timing=True,
                read_timeout=300,
            )

            stack_results[i] = result.result

        any_failed = False
        for key, value in stack_results.items():
            if not check_md5_result(
                f"{task.host.get('hostname')}:{key}", value, primary_image_md5
            ):
                any_failed = True

        if not any_failed:
            task.host.data[DataFields.PRIMARY_IMAGE_MD5_VERIFIED] = True
            task.host.data[DataFields.PRIMARY_IMAGE_IN_FLASH] = True

    else:
        result = task.run(
            task=netmiko_send_command,
            command_string=f"verify /md5 flash:{primary_image}",
            use_timing=True,
            read_timeout=300,
        )
        if check_md5_result(task.host, result.result, primary_image_md5):
            task.host.data[DataFields.PRIMARY_IMAGE_MD5_VERIFIED] = True


def verify_reload(task: Task, force: bool = True):
    if not force and task.host.data.get(DataFields.RELOAD_SET):
        return

    success, is_at_target = get_required_host_vars(task.host, [DataFields.IS_AT_TARGET])

    if not success:
        return

    if is_at_target:
        logging.info("SKIPPING verifying reload on %s: Is at Target")
        return

    success, reload_time = get_required_host_vars(task.host, [DataFields.RELOAD_TIME])

    if not success:
        return

    command = "show reload"

    result = task.run(task=netmiko_send_command, command_string=command)

    if "no reload" in result.result.lower():
        logging.error("No reload scheduled on %s: %s", task.host, result.result)
        task.host[DataFields.RELOAD_SET] = False
        return

    for part in reload_time.split():
        test_part = part.lower()
        test_part = (
            test_part[-1] if test_part[0] == "0" and len(test_part) == 2 else test_part
        )
        if (" " + test_part) not in result.result.lower():
            logging.error(
                "Reload not scheduled correctly %s: %s", task.host, result.result
            )
            task.host[DataFields.RELOAD_SET] = False
            return

    logging.info("Reload scheduled on %s", task.host)
    task.host[DataFields.RELOAD_SET] = True


def check_no_reload(task: Task):
    success, is_at_target = get_required_host_vars(task.host, [DataFields.IS_AT_TARGET])

    if not success:
        return

    command = "show reload"

    result = task.run(task=netmiko_send_command, command_string=command)

    time = "no reload"
    if time not in result.result.lower():
        logging.info("No reload scheduled on %s: %s", task.host, result.result)
        task.host[DataFields.RELOAD_SET] = False
        return

    if is_at_target:
        logging.warning("Reload scheduled on %s: %s", task.host, result.result)
    task.host[DataFields.RELOAD_SET] = True
