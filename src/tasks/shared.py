from nornir.core.task import Task


def stack_flash_format(task: Task) -> str:
    return (
        "flash{num}"
        if "2960" in task.host.get("device_type", {}).get("model", "")
        else "flash-{num}"
    )
