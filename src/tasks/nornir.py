import logging
import os

from rich import print  # pylint: disable=W0622
from rich.prompt import Prompt, Confirm
from nornir.core.filter import F
from nornir.core.task import Task


from classes.config import Config
from utils.data_fields import DataFields

CONFIG = Config()


def edit_primary_image_md5():
    """Change the primary image md5 for all hosts with that image"""

    image_to_md5 = {}
    for host in CONFIG.nornir.inventory.hosts.values():
        primary_image = host.get(DataFields.PRIMARY_IMAGE)
        md5 = host.get(DataFields.PRIMARY_IMAGE_MD5)

        if image_to_md5.get(primary_image) is None and md5 is not None:
            image_to_md5[primary_image] = md5

    for i, (image, md5) in enumerate(image_to_md5.items()):
        print(f"{i + 1}. {image}: {md5}")

    exit_index = len(image_to_md5.keys()) + 1
    print(f"{exit_index}. Exit")

    selection = int(
        Prompt.ask(
            "Select an image to edit or add a new image",
            choices=[str(i + 1) for i in range(len(image_to_md5.keys()))]
            + [str(exit_index)],
        )
    )

    if selection == exit_index:
        return

    image = list(image_to_md5.keys())[selection - 1]
    md5 = Prompt.ask(f"New MD5 for {image}")

    if Confirm.ask(f"Set MD5 for {image} to: {md5}"):
        CONFIG.nornir.run(task=_edit_primary_image_md5, primary_image=image, md5=md5)


def _edit_primary_image_md5(task: Task, primary_image, md5):
    if task.host.get(DataFields.PRIMARY_IMAGE) == primary_image:
        task.host.data[DataFields.PRIMARY_IMAGE_MD5] = md5


def get_primary_image_data():
    """Interactive prompt to set primary image data for all hosts per group"""
    image_data = []
    group_to_image_map = {}

    for group in CONFIG.nornir.inventory.groups:
        if not group.startswith("device_type"):
            continue

        print(f"[cyan bold]Group {group}")
        for i, v in enumerate(image_data):
            print(f"{i + 1}. {v[DataFields.PRIMARY_IMAGE]}")
        print(f"{len(image_data) + 1}. Add a new image")
        print(f"{len(image_data) + 2}. Exit")

        selection = Prompt.ask(
            "Select an image to edit or add a new image",
            choices=[str(i + 1) for i in range(len(image_data))]
            + [str(len(image_data) + 1), str(len(image_data) + 2)],
        )

        if selection == str(len(image_data) + 1):
            image_name = Prompt.ask(
                f"Enter the primary image for [cyan bold]{group}[/]"
            )
            image_md5 = Prompt.ask(f"Enter the md5 for [cyan bold]{image_name}[/]")

            filepath = os.path.join(CONFIG.env.image_folder, image_name)
            if not os.path.exists(filepath):
                logging.error("Image file not found: %s", filepath)
                return

            size = os.path.getsize(filepath)

            image_data.append(
                {
                    DataFields.PRIMARY_IMAGE: image_name,
                    DataFields.PRIMARY_IMAGE_MD5: image_md5,
                    DataFields.PRIMARY_IMAGE_SIZE: size,
                }
            )
            group_to_image_map[group] = len(image_data) - 1
            continue

        if selection == str(len(image_data) + 2):
            return

        group_to_image_map[group] = int(selection) - 1

    CONFIG.nornir.run(
        task=_set_primary_image_data,
        group_to_image_map=group_to_image_map,
        image_data=image_data,
    )


def _set_primary_image_data(task: Task, group_to_image_map, image_data):
    for group_obj in task.host.groups:
        group = str(group_obj)
        if group_to_image_map.get(group) is not None:
            task.host.data[DataFields.PRIMARY_IMAGE] = image_data[
                group_to_image_map[group]
            ][DataFields.PRIMARY_IMAGE]

            task.host.data[DataFields.PRIMARY_IMAGE_MD5] = image_data[
                group_to_image_map[group]
            ][DataFields.PRIMARY_IMAGE_MD5]

            task.host.data[DataFields.PRIMARY_IMAGE_SIZE] = image_data[
                group_to_image_map[group]
            ][DataFields.PRIMARY_IMAGE_SIZE]

            logging.info(
                "Setting primary image for %s: %s",
                task.host,
                task.host.data[DataFields.PRIMARY_IMAGE],
            )
            return

    logging.error("No matching group found for %s", task.host)


def print_single_field(task: Task, field):
    print(f"{task.host}: {task.host.get(field)}")


def set_single_field(task: Task, field, value):
    task.host.data[field] = value


def select_single_host(host: str):
    removed_hosts = []
    for removed_host in CONFIG.nornir.filter(~F(name__startswith=host)).inventory.hosts:
        removed_hosts.append(removed_host)
    CONFIG.nornir = CONFIG.nornir.filter(F(name__startswith=host))

    if len(removed_hosts) == 0:
        logging.warning("No hosts found to remove")
        return

    print(f"[cyan bold]{len(removed_hosts)} [yellow]host(s) removed")

    if Confirm.ask("Log removed hosts"):
        for removed_host in removed_hosts:
            logging.info("Removing host: %s", removed_host)


def remove_hosts(hosts: list[str]):
    removed_hosts = []
    for host in hosts:
        for host in CONFIG.nornir.filter(F(name__startswith=host)).inventory.hosts:
            removed_hosts.append(host)
        CONFIG.nornir = CONFIG.nornir.filter(~F(name__startswith=host))

    if len(removed_hosts) == 0:
        logging.warning("No hosts found to remove")
        return

    print(f"[cyan bold]{len(removed_hosts)} [yellow]host(s) removed")

    if Confirm.ask("Log removed hosts"):
        for host in removed_hosts:
            logging.info("Removed host: %s", host)
