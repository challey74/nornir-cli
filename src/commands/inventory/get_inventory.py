"""Commands to get inventory from Netbox or locally."""

from typing import Any, Optional

import inspect
import os

from nornir import InitNornir
from rich import print  # pylint: disable=W0622
from rich.prompt import Prompt

import typer

from commands.inventory.manage_inventory import set_default_credentials, load_inventory
from classes.config import Config
from utils.nbcd_filters import (
    filter_fix_stack_hostname,
    filter_non_conforming_hostnames,
)


CONFIG = Config()


def _user_select_get_inventory():
    while True:
        print("Select an option to get inventory:")

        options = [
            "Load Inventory",
            "Get Inventory from Local Files",
        ]

        for i, option in enumerate(options):
            print(f"{i+1}. {option}")

        choice = int(Prompt.ask("Enter option number: "))

        if choice not in range(1, len(options) + 1):
            print("Invalid option.")
            continue

        match choice:
            case 1:
                load_inventory()
                return
            case 2:
                folder_path = Prompt.ask("Enter folder path to local inventory.")
                get_inventory(folder_path=folder_path)
                return


def _parse_array(value: str, v_type) -> list[str]:
    """Parse a comma-separated string into a list, handling spaces and quotes."""
    if not value:
        return []
    return [v_type(item.strip()) for item in value.split(",")]


def get_inventory(
    airflow: Optional[str] = typer.Option(
        default=None,
        help="Direction of airflow.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    airflow__n: Optional[str] = typer.Option(
        default=None,
        help="Direction of airflow (negative).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    asset_tag: Optional[str] = typer.Option(
        default=None,
        help="Asset tag(s).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    asset_tag__n: Optional[str] = typer.Option(
        default=None,
        help="Asset tag(s) (negative).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    asset_tag__ic: Optional[str] = typer.Option(
        default=None,
        help="Asset tag(s) (case-insensitive contains).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    asset_tag__nic: Optional[str] = typer.Option(
        default=None,
        help="Asset tag(s) (negative case-insensitive contains).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    asset_tag__ie: Optional[str] = typer.Option(
        default=None,
        help="Asset tag(s) (case-insensitive exact match).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    asset_tag__nie: Optional[str] = typer.Option(
        default=None,
        help="Asset tag(s) (negative case-insensitive exact match).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    asset_tag__iew: Optional[str] = typer.Option(
        default=None,
        help="Asset tag(s) (case-insensitive ends with).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    asset_tag__niew: Optional[str] = typer.Option(
        default=None,
        help="Asset tag(s) (negative case-insensitive ends with).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    asset_tag__isw: Optional[str] = typer.Option(
        default=None,
        help="Asset tag(s) (case-insensitive starts with).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    asset_tag__nisw: Optional[str] = typer.Option(
        default=None,
        help="Asset tag(s) (negative case-insensitive starts with).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    cluster_id: Optional[str] = typer.Option(
        default=None,
        help="VM cluster ID(s).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    cluster_id__n: Optional[str] = typer.Option(
        default=None,
        help="VM cluster ID(s) (negative).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    config_template_id: Optional[str] = typer.Option(
        default=None,
        help="Config template ID(s).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    config_template_id__n: Optional[str] = typer.Option(
        default=None,
        help="Config template ID(s) (negative).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    console_ports: Optional[bool] = typer.Option(
        default=None,
        help="Has console ports.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    console_server_ports: Optional[bool] = typer.Option(
        default=None,
        help="Has console server ports.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    contact: Optional[str] = typer.Option(
        default=None,
        help="Contact ID(s).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    contact__n: Optional[str] = typer.Option(
        default=None,
        help="Contact ID(s) (negative).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    contact_group: Optional[str] = typer.Option(
        default=None,
        help="Contact group ID(s).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    contact_group__n: Optional[str] = typer.Option(
        default=None,
        help="Contact group ID(s) (negative).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    contact_role: Optional[str] = typer.Option(
        default=None,
        help="Contact role ID(s).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    contact_role__n: Optional[str] = typer.Option(
        default=None,
        help="Contact role ID(s) (negative).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    created: Optional[str] = typer.Option(
        default=None,
        help="Created timestamp.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    created__gte: Optional[str] = typer.Option(
        default=None,
        help="Created on or after timestamp.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    created__lte: Optional[str] = typer.Option(
        default=None,
        help="Created on or before timestamp.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    created__n: Optional[str] = typer.Option(
        default=None,
        help="Created timestamp(s) (negative).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    created_by_request: Optional[str] = typer.Option(
        default=None,
        help="Created by request ID.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    description: Optional[str] = typer.Option(
        default=None,
        help="Description.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    description__n: Optional[str] = typer.Option(
        default=None,
        help="Description (negative).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    description__ic: Optional[str] = typer.Option(
        default=None,
        help="Description (case-insensitive contains).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    description__nic: Optional[str] = typer.Option(
        default=None,
        help="Description (negative case-insensitive contains).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    description__ie: Optional[str] = typer.Option(
        default=None,
        help="Description (case-insensitive exact match).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    description__nie: Optional[str] = typer.Option(
        default=None,
        help="Description (negative case-insensitive exact match).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    description__iew: Optional[str] = typer.Option(
        default=None,
        help="Description (case-insensitive ends with).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    description__niew: Optional[str] = typer.Option(
        default=None,
        help="Description (negative case-insensitive ends with).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    description__isw: Optional[str] = typer.Option(
        default=None,
        help="Description (case-insensitive starts with).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    description__nisw: Optional[str] = typer.Option(
        default=None,
        help="Description (negative case-insensitive starts with).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    device_bays: Optional[bool] = typer.Option(
        default=None,
        help="Has device bays.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    device_type: Optional[str] = typer.Option(
        default=None,
        help="Device type (slug).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    device_type__n: Optional[str] = typer.Option(
        default=None,
        help="Device type (slug) (negative).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    device_type_id: Optional[str] = typer.Option(
        default=None,
        help="Device type ID(s).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    device_type_id__n: Optional[str] = typer.Option(
        default=None,
        help="Device type ID(s) (negative).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    face: Optional[str] = typer.Option(
        default=None,
        help="Face orientation.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    face__n: Optional[str] = typer.Option(
        default=None,
        help="Face orientation (negative).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    has_oob_ip: Optional[bool] = typer.Option(
        default=None,
        help="Has an out-of-band IP.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    has_primary_ip: Optional[bool] = typer.Option(
        default=None,
        help="Has a primary IP.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    id: Optional[str] = typer.Option(
        default=None,
        help="Device ID(s).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    id__n: Optional[str] = typer.Option(
        default=None,
        help="Device ID(s) (negative).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    id__gt: Optional[str] = typer.Option(
        default=None,
        help="Greater than ID.",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    id__gte: Optional[str] = typer.Option(
        default=None,
        help="Greater than or equal to ID.",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    id__lt: Optional[str] = typer.Option(
        default=None,
        help="Less than ID.",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    id__lte: Optional[str] = typer.Option(
        default=None,
        help="Less than or equal to ID.",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    interfaces: Optional[bool] = typer.Option(
        default=None,
        help="Has interfaces.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    is_full_depth: Optional[bool] = typer.Option(
        default=None,
        help="Is full depth.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    last_updated: Optional[str] = typer.Option(
        default=None,
        help="Last updated timestamp.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    last_updated__n: Optional[str] = typer.Option(
        default=None,
        help="Last updated timestamp(s) (negative).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    last_updated__gte: Optional[str] = typer.Option(
        default=None,
        help="Last updated on or after timestamp.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    last_updated__lte: Optional[str] = typer.Option(
        default=None,
        help="Last updated on or before timestamp.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    latitude: Optional[float] = typer.Option(
        default=None,
        help="Latitude.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    latitude__gt: Optional[float] = typer.Option(
        default=None,
        help="Greater than latitude.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    latitude__gte: Optional[float] = typer.Option(
        default=None,
        help="Greater than or equal to latitude.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    latitude__lt: Optional[float] = typer.Option(
        default=None,
        help="Less than latitude.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    latitude__lte: Optional[float] = typer.Option(
        default=None,
        help="Less than or equal to latitude.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    local_context_data: Optional[bool] = typer.Option(
        default=None,
        help="Has local config context data.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    location_id__n: Optional[str] = typer.Option(
        default=None,
        help="Location ID(s) (negative).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    longitude: Optional[float] = typer.Option(
        default=None,
        help="Longitude.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    longitude__n: Optional[float] = typer.Option(
        default=None,
        help="Longitude (negative).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    longitude__gt: Optional[float] = typer.Option(
        default=None,
        help="Greater than longitude.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    longitude__gte: Optional[float] = typer.Option(
        default=None,
        help="Greater than or equal to longitude.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    longitude__lt: Optional[float] = typer.Option(
        default=None,
        help="Less than longitude.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    longitude__lte: Optional[float] = typer.Option(
        default=None,
        help="Less than or equal to longitude.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    mac_address: Optional[str] = typer.Option(
        default=None,
        help="MAC address(es).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    mac_address__n: Optional[str] = typer.Option(
        default=None,
        help="MAC address(es) (negative).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    mac_address__ic: Optional[str] = typer.Option(
        default=None,
        help="MAC address(es) (case-insensitive contains).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    mac_address__nic: Optional[str] = typer.Option(
        default=None,
        help="MAC address(es) (negative case-insensitive contains).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    mac_address__ie: Optional[str] = typer.Option(
        default=None,
        help="MAC address(es) (case-insensitive exact match).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    mac_address__nie: Optional[str] = typer.Option(
        default=None,
        help="MAC address(es) (negative case-insensitive exact match).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    mac_address__iew: Optional[str] = typer.Option(
        default=None,
        help="MAC address(es) (case-insensitive ends with).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    mac_address__niew: Optional[str] = typer.Option(
        default=None,
        help="MAC address(es) (negative case-insensitive ends with).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    mac_address__isw: Optional[str] = typer.Option(
        default=None,
        help="MAC address(es) (case-insensitive starts with).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    mac_address__nisw: Optional[str] = typer.Option(
        default=None,
        help="MAC address(es) (negative case-insensitive starts with).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    manufacturer: Optional[str] = typer.Option(
        default=None,
        help="Manufacturer (slug).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    manufacturer__n: Optional[str] = typer.Option(
        default=None,
        help="Manufacturer (slug) (negative).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    manufacturer_id: Optional[str] = typer.Option(
        default=None,
        help="Manufacturer (ID).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    manufacturer_id__n: Optional[str] = typer.Option(
        default=None,
        help="Manufacturer (ID) (negative).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    model: Optional[str] = typer.Option(
        default=None,
        help="Device model (slug).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    model__n: Optional[str] = typer.Option(
        default=None,
        help="Device model (slug) (negative).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    module_bays: Optional[bool] = typer.Option(
        default=None,
        help="Has module bays.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    name: Optional[str] = typer.Option(
        default=None,
        help="Device name(s).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    name__n: Optional[str] = typer.Option(
        default=None,
        help="Device name(s) (negative).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    name__ic: Optional[str] = typer.Option(
        default=None,
        help="Device name(s) (case-insensitive contains).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    name__nic: Optional[str] = typer.Option(
        default=None,
        help="Device name(s) (negative case-insensitive contains).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    name__ie: Optional[str] = typer.Option(
        default=None,
        help="Device name(s) (case-insensitive exact match).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    name__nie: Optional[str] = typer.Option(
        default=None,
        help="Device name(s) (negative case-insensitive exact match).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    name__iew: Optional[str] = typer.Option(
        default=None,
        help="Device name(s) (case-insensitive ends with).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    name__niew: Optional[str] = typer.Option(
        default=None,
        help="Device name(s) (negative case-insensitive ends with).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    name__isw: Optional[str] = typer.Option(
        default=None,
        help="Device name(s) (case-insensitive starts with).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    name__nisw: Optional[str] = typer.Option(
        default=None,
        help="Device name(s) (negative case-insensitive starts with).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    oob_ip_id: Optional[str] = typer.Option(
        default=None,
        help="OOB IP (ID).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    oob_ip_id__n: Optional[str] = typer.Option(
        default=None,
        help="OOB IP (ID) (negative).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    parent_device_id: Optional[str] = typer.Option(
        default=None,
        help="Parent Device (ID).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    parent_device_id__n: Optional[str] = typer.Option(
        default=None,
        help="Parent Device (ID) (negative).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    pass_through_ports: Optional[bool] = typer.Option(
        default=None,
        help="Has pass-through ports.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    platform: Optional[str] = typer.Option(
        default=None,
        help="Platform (slug).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    platform__n: Optional[str] = typer.Option(
        default=None,
        help="Platform (slug) (negative).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    platform_id: Optional[str] = typer.Option(
        default=None,
        help="Platform (ID).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    platform_id__n: Optional[str] = typer.Option(
        default=None,
        help="Platform (ID) (negative).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    position: Optional[float] = typer.Option(
        default=None,
        help="Position.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    position__n: Optional[float] = typer.Option(
        default=None,
        help="Position (negative).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    position__gt: Optional[float] = typer.Option(
        default=None,
        help="Greater than position.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    position__gte: Optional[float] = typer.Option(
        default=None,
        help="Greater than or equal to position.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    position__lt: Optional[float] = typer.Option(
        default=None,
        help="Less than position.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    position__lte: Optional[float] = typer.Option(
        default=None,
        help="Less than or equal to position.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    power_outlets: Optional[bool] = typer.Option(
        default=None,
        help="Has power outlets.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    power_ports: Optional[bool] = typer.Option(
        default=None,
        help="Has power ports.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    primary_ip4_id: Optional[str] = typer.Option(
        default=None,
        help="Primary IPv4 (ID).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    primary_ip4_id__n: Optional[str] = typer.Option(
        default=None,
        help="Primary IPv4 (ID) (negative).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    primary_ip6_id: Optional[str] = typer.Option(
        default=None,
        help="Primary IPv6 (ID).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    primary_ip6_id__n: Optional[str] = typer.Option(
        default=None,
        help="Primary IPv6 (ID) (negative).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    q: Optional[str] = typer.Option(
        default=None,
        help="Search query.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    rack_id: Optional[str] = typer.Option(
        default=None,
        help="Rack (ID).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    rack_id__n: Optional[str] = typer.Option(
        default=None,
        help="Rack (ID) (negative).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    region: Optional[str] = typer.Option(
        default=None,
        help="Region (slug).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    region__n: Optional[str] = typer.Option(
        default=None,
        help="Region (slug) (negative).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    region_id: Optional[str] = typer.Option(
        default=None,
        help="Region (ID).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    region_id__n: Optional[str] = typer.Option(
        default=None,
        help="Region (ID) (negative).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    role: Optional[str] = typer.Option(
        default=None,
        help="Role (slug).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    role__n: Optional[str] = typer.Option(
        default=None,
        help="Role (slug) (negative).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    role_id: Optional[str] = typer.Option(
        default=None,
        help="Role (ID).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    role_id__n: Optional[str] = typer.Option(
        default=None,
        help="Role (ID) (negative).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    serial: Optional[str] = typer.Option(
        default=None,
        help="Serial number.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    serial__n: Optional[str] = typer.Option(
        default=None,
        help="Serial number (negative).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    serial__ic: Optional[str] = typer.Option(
        default=None,
        help="Serial number (case-insensitive contains).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    serial__nic: Optional[str] = typer.Option(
        default=None,
        help="Serial number (negative case-insensitive contains).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    serial__ie: Optional[str] = typer.Option(
        default=None,
        help="Serial number (case-insensitive exact match).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    serial__nie: Optional[str] = typer.Option(
        default=None,
        help="Serial number (negative case-insensitive exact match).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    serial__iew: Optional[str] = typer.Option(
        default=None,
        help="Serial number (case-insensitive ends with).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    serial__niew: Optional[str] = typer.Option(
        default=None,
        help="Serial number (negative case-insensitive ends with).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    serial__isw: Optional[str] = typer.Option(
        default=None,
        help="Serial number (case-insensitive starts with).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    serial__nisw: Optional[str] = typer.Option(
        default=None,
        help="Serial number (negative case-insensitive starts with).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    site: Optional[str] = typer.Option(
        default=None,
        help="Site name (slug).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    site__n: Optional[str] = typer.Option(
        default=None,
        help="Site name (slug) (negative).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    site_group: Optional[str] = typer.Option(
        default=None,
        help="Site group (slug).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    site_group__n: Optional[str] = typer.Option(
        default=None,
        help="Site group (slug) (negative).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    site_group_id: Optional[str] = typer.Option(
        default=None,
        help="Site group (ID).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    site_group_id__n: Optional[str] = typer.Option(
        default=None,
        help="Site group (ID) (negative).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    site_id: Optional[str] = typer.Option(
        default=None,
        help="Site (ID).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    site_id__n: Optional[str] = typer.Option(
        default=None,
        help="Site (ID) (negative).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    status: Optional[str] = typer.Option(
        default=None,
        help="Status.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    status__n: Optional[str] = typer.Option(
        default=None,
        help="Status (negative).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    tag: Optional[str] = typer.Option(
        default=None,
        help="Tag(s).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    tag__n: Optional[str] = typer.Option(
        default=None,
        help="Tag(s) (negative).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    tenant: Optional[str] = typer.Option(
        default=None,
        help="Tenant (slug).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    tenant__n: Optional[str] = typer.Option(
        default=None,
        help="Tenant (slug) (negative).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    tenant_group: Optional[str] = typer.Option(
        default=None,
        help="Tenant Group (slug).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    tenant_group__n: Optional[str] = typer.Option(
        default=None,
        help="Tenant Group (slug) (negative).",
        rich_help_panel="Filters",
        show_default=False,
    ),
    tenant_group_id: Optional[str] = typer.Option(
        default=None,
        help="Tenant Group (ID).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    tenant_group_id__n: Optional[str] = typer.Option(
        default=None,
        help="Tenant Group (ID) (negative).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    tenant_id: Optional[str] = typer.Option(
        default=None,
        help="Tenant (ID).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    tenant_id__n: Optional[str] = typer.Option(
        default=None,
        help="Tenant (ID) (negative).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    vc_position: Optional[int] = typer.Option(
        default=None,
        help="Virtual Chassis position.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    vc_position__gt: Optional[int] = typer.Option(
        default=None,
        help="Greater than Virtual Chassis position.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    vc_position__gte: Optional[int] = typer.Option(
        default=None,
        help="Greater than or equal to Virtual Chassis position.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    vc_position__lt: Optional[int] = typer.Option(
        default=None,
        help="Less than Virtual Chassis position.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    vc_position__lte: Optional[int] = typer.Option(
        default=None,
        help="Less than or equal to Virtual Chassis position.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    vc_priority: Optional[int] = typer.Option(
        default=None,
        help="Virtual Chassis priority.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    vc_priority__gt: Optional[int] = typer.Option(
        default=None,
        help="Greater than Virtual Chassis priority.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    vc_priority__gte: Optional[int] = typer.Option(
        default=None,
        help="Greater than or equal to Virtual Chassis priority.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    vc_priority__lt: Optional[int] = typer.Option(
        default=None,
        help="Less than Virtual Chassis priority.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    vc_priority__lte: Optional[int] = typer.Option(
        default=None,
        help="Less than or equal to Virtual Chassis priority.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    virtual_chassis_id: Optional[str] = typer.Option(
        default=None,
        help="Virtual chassis (ID).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    virtual_chassis_id__n: Optional[str] = typer.Option(
        default=None,
        help="Virtual chassis (ID) (negative).",
        rich_help_panel="ID Filters",
        show_default=False,
    ),
    virtual_chassis_member: Optional[bool] = typer.Option(
        default=None,
        help="Is a virtual chassis member.",
        rich_help_panel="Filters",
        show_default=False,
    ),
    folder_path: Optional[str] = typer.Option(
        default=None,
        help=(
            "Folder path to local inventory to be imported with hosts, groups and "
            "defaults yaml files."
        ),
        rich_help_panel="Files",
        show_default=False,
    ),
    names_file_path: Optional[str] = typer.Option(
        default=None,
        help="File path to a text file with hostnames to be imported via Netbox.",
        rich_help_panel="Files",
        show_default=False,
    ),
):
    """Get inventory from Netbox using filter parameters or a file with a list of names.

    Filter parameters can be passed as comma-separated strings with or without spaces and quotes.
    For local inventory, use --folder-path option.
    For importing specific hostnames from Netbox, use --names-file-path option.
    """
    filter_params: dict[str, Any] = {}

    # Handle folder path option first
    if folder_path is not None:
        if any(
            locals()[param] is not None
            for param in inspect.signature(get_inventory).parameters
            if param not in ["folder_path"]
        ):
            raise ValueError(
                "Cannot specify both folder_path and other filter parameters."
            )

        if not os.path.isdir(folder_path):
            raise FileNotFoundError(
                f"Folder path {folder_path} does not exist or is not a directory."
            )

        _get_nornir_with_local_inventory(folderpath=folder_path)
        return

    # Handle names file path option
    if names_file_path is not None:
        if not os.path.isfile(names_file_path):
            raise FileNotFoundError(f"File path {names_file_path} does not exist.")

        with open(names_file_path, "r") as file:
            filter_params = {
                "name__ic": [name.lower().strip() for name in file.readlines()],
            }
            return _get_nornir_with_netbox_inventory(filter_params)

    # Process all parameters
    for param_name, param_value in locals().items():
        # Skip local vars, special parameters, and None values
        if (
            param_name in ["filter_params", "folder_path", "names_file_path"]
            or param_value is None
        ):
            continue

        if (
            isinstance(param_value, bool)
            or isinstance(param_value, int)
            or isinstance(param_value, float)
        ):
            filter_params[param_name] = param_value
            continue

        # handle non-array strings
        if any(
            param_name.startswith(prefix)
            for prefix in [
                "airflow",
                "face",
                "ordering",
                "q",
                "created_by_request",
                "modified_by_request",
                "updated_by_request",
            ]
        ):
            filter_params[param_name] = param_value

        # handle int arrays
        if any(
            param_name.startswith(prefix)
            for prefix in [
                "cluster_id",
                "config_template_id",
                "contact",
                "contact_group",
                "contact_role",
                "device_type_id",
                "id",
                "location_id",
                "manufacturer_id",
                "oob_ip_id",
                "parent_device_id",
                "platform_id",
                "primary_ip4_id",
                "primary_ip6_id",
                "rack_id",
                "region",
                "region_id",
                "role_id",
                "site_group",
                "site_group_id",
                "site_id",
                "tenant_group",
                "tenant_group_id",
                "tenant_id",
                "vc_position",
                "vc_priority",
                "virtual_chassis_id",
            ]
        ):
            filter_params[param_name] = _parse_array(param_value, int)
            continue

        # handle float arrays
        if any(
            param_name.startswith(prefix)
            for prefix in ["latitude", "longitude", "position"]
        ):
            filter_params[param_name] = _parse_array(param_value, float)
            continue

        # handle string arrays
        print(f"[yellow]param_name: {param_name}, param_value: {param_value}")
        filter_params[param_name] = _parse_array(param_value, str)

    print(f"[yellow]Filter Params in use [green]{filter_params}")

    _get_nornir_with_netbox_inventory(filter_params)

    hosts = CONFIG.nornir.inventory.dict()["hosts"]
    print(f"[yellow]{len(hosts)} Hosts in Inventory")

    i = 0
    for host in hosts:
        print(f"[cyan]{host}")
        i += 1
        if i == 3:
            print("...")
            break


def _get_nornir_with_local_inventory(folderpath: str):
    """initialize Nornir instance with local inventory with standard configuration.
    Requires .env file with TACACS_USER and TACACS_PASS variables."""

    if not folderpath:
        raise ValueError("No folderpath provided.")

    if not os.path.isdir(folderpath):
        raise FileNotFoundError(
            f"Folder path does not exist or is not a directory: {folderpath}"
        )

    host_file = os.path.join(folderpath, "hosts.yaml")
    group_file = os.path.join(folderpath, "groups.yaml")
    defaults_file = os.path.join(folderpath, "defaults.yaml")
    metadata_file = os.path.join(folderpath, "metadata.yaml")

    if not all(os.path.exists(file) for file in [host_file, group_file, defaults_file]):
        raise FileNotFoundError(
            f"Files not found in folder path: {folderpath}. \
            Required files: hosts.yaml, groups.yaml, defaults.yaml."
        )

    nornir = InitNornir(
        inventory={
            "plugin": "SimpleInventory",
            "options": {
                "host_file": os.path.join(folderpath, "hosts.yaml"),
                "group_file": os.path.join(folderpath, "groups.yaml"),
                "defaults_file": os.path.join(folderpath, "defaults.yaml"),
            },
        },
        runner={"plugin": "threaded", "options": {"num_workers": 100}},
        logging={"enabled": False},
    )

    filter_non_conforming_hostnames(nornir)
    filter_fix_stack_hostname(nornir)

    CONFIG.nornir = nornir
    if os.path.exists(metadata_file):
        CONFIG.metadata.set_metadata_from_file(metadata_file)
    else:
        CONFIG.metadata.set_metadata_from_input(filter_parameters=None)


def _get_nornir_with_netbox_inventory(filter_parameters: dict[str, str]):
    """initialize Nornir instance with Netbox inventory with standard configuration.
        Requires .env file with netbox_url and NETBOX_TOKEN variables.

    Args:
        filter_parameters (dict[str, str], optional): filters NetBox inventory based \
        on supplied parameters such as 'site_id': '15073'.
        Defaults to empty Dictionary. For more info go to \
        github.com/wvandeun/nornir_netbox/blob/develop/docs/usage.md.

    Returns:
        Nornir: Nornir object used to run tasks.
    """

    if not filter_parameters:
        raise ValueError("No filter parameters.")

    netbox_url = CONFIG.env.netbox_url
    netbox_token = CONFIG.env.netbox_token

    if not netbox_url or not netbox_token:
        raise ValueError("No NetBox URL or Token found in environment variables.")

    nornir = InitNornir(
        inventory={
            "plugin": "NetBoxInventory2",
            "options": {
                "nb_url": netbox_url,
                "nb_token": netbox_token,
                "filter_parameters": filter_parameters,
            },
        },
        runner={"plugin": "threaded", "options": {"num_workers": 100}},
        logging={"enabled": False},
    )

    filter_non_conforming_hostnames(nornir)
    filter_fix_stack_hostname(nornir)

    CONFIG.nornir = nornir
    CONFIG.metadata.set_metadata_from_input(filter_parameters)

    set_default_credentials(prompt=False)
