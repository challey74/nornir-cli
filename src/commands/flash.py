"""Module for working with flash on network devices."""

from typing import Optional

import typer

from classes.config import Config

import tasks.flash
import tasks.transfer

CONFIG = Config()


def delete_archives(
    year: Optional[int] = typer.Option(
        None, help="Year to delete archives prior to.", show_default=True
    ),
):
    CONFIG.nornir.run(task=tasks.flash.delete_old_archives, prior_to_year=year)


def is_primary_image_in_flash():
    CONFIG.nornir.run(task=tasks.flash.is_primary_image_in_flash)


def get_images_to_delete():
    """Get the images on a device that can be deleted."""

    CONFIG.nornir.run(task=tasks.flash.get_images_to_delete)


def get_free_flash(
    size_to_check: Optional[int] = typer.Option(
        None,
        help="Size in bytes to check against the available flash.",
        show_default=True,
    ),
):
    """Get the free flash on a device and compare it to a size_to_check if provided.

    Args:
        size_to_check (int, optional): Size in bytes to check against \
        the available flash. Defaults to None.
    """

    CONFIG.nornir.run(
        task=tasks.flash.get_free_flash,
        size_to_check=size_to_check,
    )


def delete_unused_images():
    """Delete images on a device that are not in use."""

    CONFIG.nornir.run(task=tasks.flash.delete_unused_images)


def get_and_delete_unused_images():
    """Get the images to delete and delete them."""

    CONFIG.nornir.run(task=tasks.flash.get_images_to_delete)
    CONFIG.nornir.run(task=tasks.flash.delete_unused_images)


def transfer_image():
    """Transfer an image to a device."""

    CONFIG.nornir.run(task=tasks.transfer.transfer_image)


def copy_image_to_stack():
    """Copy an image to the stack."""

    CONFIG.nornir.run(task=tasks.flash.copy_image_to_stack)


def check_for_image_on_stack(
    force: bool = typer.Option(False, is_flag=True, help="Force the check."),
):
    """Check for an image on the stack."""

    CONFIG.nornir.run(task=tasks.flash.is_primary_image_in_flash_stack, force=force)
