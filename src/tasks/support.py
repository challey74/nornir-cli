from nornir.core import Task

from utils.data_fields import DataFields


def supports_ssh_bulk_mode(task: Task):
    if "2960" in task.host.get("device_type", {}).get("model", ""):
        task.host.data[DataFields.SUPPORTS_SSH_BULK_MODE] = False

    task.host.data[DataFields.SUPPORTS_SSH_BULK_MODE] = True
