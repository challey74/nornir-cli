from classes.config import Config

import tasks.workflows
import tasks.configure
import tasks.nornir
import tasks.device_info
import tasks.flash
import tasks.verify


CONFIG = Config()


def check_transfer_completed():
    """Checks if the primary image is in flash and verified.
    Runs md5 verification if image is in flash but not verified yet."""

    CONFIG.nornir.run(task=tasks.workflows.check_transfer_completed)


def check_hostname():
    """Checks if the hostname resolves to ip on host in inventory."""

    CONFIG.nornir.run(task=tasks.workflows.is_correct_hostname)


def transfer_and_verify_images(skip_dns_check: bool = False):
    """Checks if primary image is in flash, transfers image if not,
    and verifies MD5 checksum."""

    CONFIG.nornir.run(
        task=tasks.workflows.transfer_and_verify_image, skip_dns_check=skip_dns_check
    )
