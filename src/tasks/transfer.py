import logging
import os

from nornir.core.task import Task
from nornir_netmiko.tasks import netmiko_file_transfer

from classes.config import Config
from utils.data_fields import DataFields, get_required_host_vars


CONFIG = Config()

# TODO: Set the exec-timeout to 0 0 before and then reset to config time after


def transfer_image(task: Task):
    success, primary_image, primary_image_in_flash, is_at_target = (
        get_required_host_vars(
            task.host,
            [
                DataFields.PRIMARY_IMAGE,
                DataFields.PRIMARY_IMAGE_IN_FLASH,
                DataFields.IS_AT_TARGET,
            ],
        )
    )

    if not success:
        return

    if is_at_target:
        logging.info("SKIPPING. %s already at target version", task.host)
        return

    if primary_image_in_flash:
        logging.info("SKIPPING. %s has %s in flash", task.host, primary_image)
        return

    os_file_name = os.path.join(CONFIG.env.image_folder, primary_image)

    logging.info("%s: Beginning Transfer", task.host)

    task.run(
        task=netmiko_file_transfer,
        source_file=os_file_name,
        socket_timeout=120,
        dest_file=primary_image,
        direction="put",
    )

    logging.info("SUCCESS %s: Transfer Completed", task.host)
