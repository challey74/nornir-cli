import logging
import re

from datetime import datetime
from typing import Any

from nornir.core.task import Task
from nornir_netmiko.tasks import netmiko_send_command

from classes.config import Config
from utils.data_fields import DataFields, get_required_host_vars, StackInfoFields
from utils.helpers import search_dict_for_key
from utils.type_defs import Version
from tasks.shared import stack_flash_format


CONFIG = Config()


def _get_flash_files(task: Any, flash_command: str) -> dict[str, Any]:
    """Get images from flash memory using specified command.
    DOES NOT CATCH EXCEPTIONS.
    """

    result = task.run(
        netmiko_send_command,
        command_string=flash_command,
        use_genie=True,
        read_timeout=300,
    )
    return result.result


def delete_old_archives(task: Task, prior_to_year: int | None = None):
    """
    Delete archive files older than specified year from flash.

    Args:
        task: Nornir task instance
        flash_contents: Dictionary of flash contents from 'dir' command
        year: Minimum year to keep, files older will be deleted (default: 2024)

    Returns:
        Result object containing list of deleted files and any errors
    """

    flash_contents = _get_flash_files(task, "dir")
    files = search_dict_for_key(flash_contents, "files")

    deleted_files = []
    errors = []

    for filename, details in files.items():
        if not filename.startswith("archive"):
            continue

        try:
            if prior_to_year is not None:
                date_str = details["last_modified_date"].split()[0:3]
                file_date = datetime.strptime(" ".join(date_str), "%b %d %Y")
                if file_date.year >= prior_to_year:
                    continue

            cmd = f"delete /force flash:/{filename}"
            result = task.run(
                task=netmiko_send_command, command_string=cmd, enable=True
            )

            if result.failed:
                errors.append(f"Failed to delete {filename}: {result.result}")
            else:
                deleted_files.append(
                    {
                        "filename": filename,
                        "date": file_date.strftime("%Y-%m-%d"),
                        "size": details["size"],
                    }
                )

        except (ValueError, KeyError) as e:
            errors.append(f"Error processing {filename}: {str(e)}")

    logging.info("Deleted %s files from %s", len(deleted_files), task.host)
    if errors:
        logging.error("%s Errors: %s", len(errors), errors)


def is_primary_image_in_flash(task: Task, force: bool = True):
    if not force and task.host.data.get(DataFields.PRIMARY_IMAGE_IN_FLASH):
        return

    (
        success,
        primary_image,
    ) = get_required_host_vars(task.host, [DataFields.PRIMARY_IMAGE])

    if not success:
        return

    flash = _get_flash_files(task, "dir")

    files = search_dict_for_key(flash, "files")

    task.host.data[DataFields.PRIMARY_IMAGE_IN_FLASH] = result = any(
        primary_image == file for file in files
    )

    if result:
        logging.info("SUCCESS: %s in flash on %s", primary_image, task.host)
    else:
        logging.info("FAIL: %s not on %s", primary_image, task.host)


def _create_image_regex(primary_image: str) -> re.Pattern:
    """Create regex pattern for matching images to delete."""
    regex_list = [re.escape(primary_image[:5]) + r".+", r"\S+.bin"]
    return re.compile("|".join(regex_list))


def _parse_file_name(file: dict[str, str] | str) -> str:
    """Extract filename from file object or string."""
    match file:
        case {"name": str() as name}:
            return name
        case str() as name:
            return name
        case _:
            raise TypeError(
                f"Expected dict with string 'name' field or string, got {type(file).__name__}. Input: {file}"
            )


def _should_delete_image(
    name: str, primary_image: str, current_image: str, ios_version: str
) -> bool:
    """Determine if an image should be deleted."""
    return (
        name != primary_image
        and name != current_image
        and not _match_ios_version(ios_version, name)
    )


def _parse_version(version: str) -> Version | None:
    """Parse a numerical version string into its components."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version)
    if not match:
        return None
    return Version(
        major=int(match.group(1)), minor=int(match.group(2)), patch=int(match.group(3))
    )


def _match_ios_version(version: str, target_string: str) -> bool:
    """
    Check if an IOS version number appears in a string, handling different formatting.
    Matches versions like:
        - "17.6.2" against both "17.6.2" and "17.02.02"
        - "15.2(4)E6" against both "15.2(4)E6" and "152-4.E6"

    Args:
        version: The version to search for (e.g., "17.6.2" or "15.2(4)E6")
        target_string: The string to search in (e.g., "asr1000-rpbase.17.6.02.SPA.pkg"
            or "c2960-lanbasek9-mz.152-4.E6.bin")

    Returns:
        bool: True if the version is found in any format in the string
    """
    if not version or not target_string:
        return False

    # Try to match the extended format first (15.2(4)E6)
    extended_match = re.match(
        r"(\d+)\.(\d+)\((\d+)\)([A-Z])(\d+)",
        version,
    )

    if extended_match:
        major, minor, patch, train, train_num = extended_match.groups()
        patterns = [
            # Original format pattern
            rf"{major}\.{minor}\({patch}\){train}{train_num}",
            # Hyphenated format pattern
            rf"{major}{minor}\-{patch}\.{train}{train_num}",
        ]
    else:
        # Handle the original version format (17.6.2)
        simple_match = re.match(r"(\d+)\.(\d+)\.(\d+)", version)
        if not simple_match:
            return False

        major, minor, patch = simple_match.groups()
        patterns = [
            rf"{major}\.{minor}\.0?{patch}(?!\d)",
        ]

    return any(bool(re.search(pattern, target_string)) for pattern in patterns)


def _process_netmiko_result(
    result: dict[str, Any] | list[Any] | str,
    compiled_regex: re.Pattern,
    primary_image: str,
    current_image: str,
    ios_version: str,
) -> set[str]:
    """Process netmiko command result and return images to delete."""

    images_to_delete = set()

    if isinstance(result, dict):
        files = search_dict_for_key(result, "files")
        for name in files:
            if re.match(compiled_regex, name) and _should_delete_image(
                name, primary_image, current_image, ios_version
            ):
                images_to_delete.add(name)
    elif isinstance(result, list):
        for file in result:
            name = _parse_file_name(file)
            if re.match(compiled_regex, name) and _should_delete_image(
                name, primary_image, current_image, ios_version
            ):
                images_to_delete.add(name)
    elif isinstance(result, str):
        for match in compiled_regex.finditer(result):
            name = match.group()
            if _should_delete_image(name, primary_image, current_image, ios_version):
                images_to_delete.add(name)
    else:
        raise TypeError(
            f"Expected dict, list or string, got {type(result).__name__}. Input: {result}"
        )

    return images_to_delete


def get_images_to_delete(task: Any) -> None:
    """Main function to identify images that should be deleted.

    This is the only public function in this module, intended to be the main entry point
    for image deletion identification functionality.

    Args:
        task: Task object containing host information and execution methods.

    Returns:
        None. Results are stored in task.host.data["images_to_delete"].
    """

    success, primary_image, current_image, ios_version, stack_info = (
        get_required_host_vars(
            task.host,
            [
                DataFields.PRIMARY_IMAGE,
                DataFields.CURRENT_IMAGE,
                DataFields.IOS_VERSION,
                DataFields.STACK_INFO,
            ],
        )
    )
    if not success:
        return

    compiled_regex = _create_image_regex(primary_image)
    images_to_delete = set()

    if stack_info[StackInfoFields.IS_STACK]:
        for num in stack_info[StackInfoFields.MEMBERS]:
            flash = stack_flash_format(task).format(num=num)
            result = _get_flash_files(task, f"show {flash}:")
            images = _process_netmiko_result(
                result, compiled_regex, primary_image, current_image, ios_version
            )
            images_to_delete.update(images)
    else:
        result = _get_flash_files(task, "show flash:")
        images_to_delete = _process_netmiko_result(
            result, compiled_regex, primary_image, current_image, ios_version
        )

    task.host.data["images_to_delete"] = images_to_delete
    if images_to_delete:
        logging.info("%s: Images to delete: %s", task.host, images_to_delete)
    else:
        logging.info("%s: No images to delete", task.host)


def get_free_flash(
    task,
    size_to_check: int | None = None,
):
    if size_to_check is None:
        success, size_to_check = get_required_host_vars(
            task.host,
            [DataFields.PRIMARY_IMAGE_SIZE],
        )

        if not success:
            return

    result = task.run(task=netmiko_send_command, command_string="dir", use_textfsm=True)
    result = result[0].result

    if not result:
        logging.error("%s: No result returned", task.host)
        return

    available_flash = result[0].get("total_free")

    if available_flash is None:
        logging.error("%s: total_free not found in result %s", task.host, result)
        return None

    if size_to_check is None:
        logging.info("%s: %s bytes available", task.host, available_flash)
        return

    if (int_flash := int(available_flash)) < size_to_check:
        logging.info(
            "%s: Not Enough Flash: %s Needed", task.host, size_to_check - int_flash
        )
        task.host.data[DataFields.FLASH_SPACE_AVAILABLE] = False
    else:
        task.host.data[DataFields.FLASH_SPACE_AVAILABLE] = True


def delete_unused_images(task: Task):
    success, images_to_delete, stack_info = get_required_host_vars(
        task.host,
        ["images_to_delete", DataFields.STACK_INFO],
    )

    if not success:
        return

    if stack_info[StackInfoFields.IS_STACK]:
        for num in stack_info[StackInfoFields.MEMBERS]:
            for image in images_to_delete:
                if image != task.host.get(
                    DataFields.PRIMARY_IMAGE
                ) and image != task.host.get(DataFields.CURRENT_IMAGE):
                    flash = stack_flash_format(task).format(num=num)
                    command = f"delete /recursive /force {flash}:{image}"
                    task.run(
                        task=netmiko_send_command,
                        read_timeout=600,
                        command_string=command,
                    )
    else:
        for image in images_to_delete:
            if image != task.host.get(
                DataFields.PRIMARY_IMAGE
            ) and image != task.host.get(DataFields.CURRENT_IMAGE):
                task.run(
                    task=netmiko_send_command,
                    read_timeout=300,
                    command_string=f"delete /recursive /force flash:{image}",
                )


def copy_image_to_stack(task: Task):
    success, primary_img, stack_info = get_required_host_vars(
        task.host,
        [DataFields.PRIMARY_IMAGE, DataFields.STACK_INFO],
    )

    if not success:
        return

    if not stack_info[StackInfoFields.IS_STACK]:
        logging.info("%s: Not a stack. Skipping copy image to stack.", task.host)
        return

    master = stack_info[StackInfoFields.MASTER]
    master_flash = stack_flash_format(task).format(num=master)
    for i in stack_info[StackInfoFields.MEMBERS]:
        if i == master or i in stack_info.get(StackInfoFields.TARGET_IN_FLASH, []):
            continue

        logging.info("Copying %s flash-%s on %s", primary_img, i, task.host)

        member_flash = stack_flash_format(task).format(num=i)
        command = f"copy {master_flash}:{primary_img} {member_flash}:{primary_img}\n\n"

        result = task.run(
            task=netmiko_send_command,
            read_timeout=7200,
            command_string=command,
        )

        if "%Warning:There is a file already existing with this name" in result.result:
            task.run(task=netmiko_send_command, command_string="n")


def is_primary_image_in_flash_stack(task: Task, force: bool = True):
    success, primary_image, stack_info = get_required_host_vars(
        task.host,
        [DataFields.PRIMARY_IMAGE, DataFields.STACK_INFO],
    )

    if not success:
        return

    if not stack_info[StackInfoFields.IS_STACK]:
        logging.info(
            "%s: Not a stack. Skipping check for primary image in flash for stacks.",
            task.host,
        )
        return

    failed = []
    if task.host.data.get(DataFields.PRIMARY_IMAGE_IN_FLASH) is None:
        task.host.data[DataFields.STACK_INFO][StackInfoFields.TARGET_IN_FLASH] = []
    for i in stack_info[StackInfoFields.MEMBERS]:
        if (
            not force
            and i
            in task.host.data[DataFields.STACK_INFO][StackInfoFields.TARGET_IN_FLASH]
        ):
            continue

        flash = stack_flash_format(task).format(num=i)
        result = task.run(
            netmiko_send_command,
            command_string=f"show {flash}:",
            use_textfsm=True,
        )

        if primary_image not in result.result:
            failed.append(i)
            continue

        task.host.data[DataFields.STACK_INFO][StackInfoFields.TARGET_IN_FLASH].append(i)

    if failed:
        logging.error(
            "%s: Primary image not found in flash for stack members: %s",
            task.host,
            failed,
        )
