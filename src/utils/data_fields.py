from collections.abc import Callable, Sequence
from enum import StrEnum, auto
from typing import Any

import logging
import yaml

from nornir.core.inventory import Host
from utils.validators import is_not_empty_string, is_positive_integer


class FieldCategory(StrEnum):
    CUSTOM = auto()
    NETBOX = auto()


class DataField:
    def __init__(
        self,
        name: str,
        t: type,
        validators: list[Callable[[Any], bool]] | None = None,
        field_category: FieldCategory = FieldCategory.NETBOX,
    ):
        self.name = name
        self.t = t
        self.validators = validators
        self.field_category = field_category

    def __repr__(self):
        return f"DataField({self.name})"

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, DataField):
            return self.name == other.name
        elif isinstance(other, str):
            return self.name == other
        return False

    def validate(self, value: Any) -> bool:
        """Validate the value is of the specified type and against the validators."""
        if issubclass(self.t, NestedDataFields):
            return self.t.validate_dict(value)

        if not isinstance(value, self.t):
            return False

        if self.validators is None:
            return True

        return all(validator(value) for validator in self.validators)


class NestedDataFields:
    """Base class for nested dict data field structures."""

    @classmethod
    def get_data_fields(cls) -> dict[str, DataField]:
        """Returns all DataField attributes of this class."""
        return {
            attr.name: attr
            for attr in cls.__dict__.values()
            if isinstance(attr, DataField)
        }

    @classmethod
    def validate_dict(cls, value: dict) -> bool:
        """Validate a dictionary against this class's DataField definitions."""
        if not isinstance(value, dict):
            return False

        data_fields = cls.get_data_fields()

        for field_name, field_value in value.items():
            if field_name in data_fields:
                if not data_fields[field_name].validate(field_value):
                    return False

        return True


class StackInfoFields(NestedDataFields):
    IS_STACK = DataField("is_stack", bool)
    MEMBERS = DataField("stack_members", list)
    MASTER = DataField("stack_master", str, [is_not_empty_string])
    TARGET_IN_FLASH = DataField("target_in_flash", bool)


class ManufacturerFields(NestedDataFields):
    """Manufacturer fields structure."""

    ID = DataField("id", int, [is_positive_integer])
    NAME = DataField("name", str, [is_not_empty_string])
    SLUG = DataField("slug", str, [is_not_empty_string])
    DISPLAY = DataField("display", str, [is_not_empty_string])
    DESCRIPTION = DataField("description", str)
    URL = DataField("url", str, [is_not_empty_string])


class DeviceTypeFields(NestedDataFields):
    """Device type fields structure."""

    ID = DataField("id", int, [is_positive_integer])
    MODEL = DataField("model", str, [is_not_empty_string])
    SLUG = DataField("slug", str, [is_not_empty_string])
    DISPLAY = DataField("display", str, [is_not_empty_string])
    DESCRIPTION = DataField("description", str)
    MANUFACTURER = DataField("manufacturer", ManufacturerFields)
    URL = DataField("url", str, [is_not_empty_string])


class SiteFields(NestedDataFields):
    """Site fields structure."""

    ID = DataField("id", int, [is_positive_integer])
    NAME = DataField("name", str, [is_not_empty_string])
    SLUG = DataField("slug", str, [is_not_empty_string])


class TenantFields(NestedDataFields):
    """Tenant fields structure."""

    ID = DataField("id", int, [is_positive_integer])
    NAME = DataField("name", str, [is_not_empty_string])
    SLUG = DataField("slug", str, [is_not_empty_string])
    DESCRIPTION = DataField("description", str)


class PlatformFields(NestedDataFields):
    """Platform fields structure."""

    ID = DataField("id", int, [is_positive_integer])
    NAME = DataField("name", str, [is_not_empty_string])
    SLUG = DataField("slug", str, [is_not_empty_string])
    DISPLAY = DataField("display", str, [is_not_empty_string])
    DESCRIPTION = DataField("description", str)
    URL = DataField("url", str, [is_not_empty_string])


class StatusFields(NestedDataFields):
    """Status fields structure."""

    LABEL = DataField("label", str, [is_not_empty_string])
    VALUE = DataField("value", str, [is_not_empty_string])


class TagFields(NestedDataFields):
    """Tag fields structure."""

    ID = DataField("id", int, [is_positive_integer])
    NAME = DataField("name", str, [is_not_empty_string])
    SLUG = DataField("slug", str, [is_not_empty_string])
    COLOR = DataField("color", str)


class MasterDeviceFields(NestedDataFields):
    """Master device fields structure for virtual chassis."""

    ID = DataField("id", int, [is_positive_integer])
    NAME = DataField("name", str, [is_not_empty_string])
    DISPLAY = DataField("display", str, [is_not_empty_string])
    DISPLAY_URL = DataField("display_url", str, [is_not_empty_string])
    URL = DataField("url", str, [is_not_empty_string])


class VirtualChassisFields(NestedDataFields):
    """Virtual chassis fields structure."""

    ID = DataField("id", int, [is_positive_integer])
    NAME = DataField("name", str, [is_not_empty_string])
    DISPLAY = DataField("display", str, [is_not_empty_string])
    DESCRIPTION = DataField("description", str)
    MEMBER_COUNT = DataField("member_count", int, [is_positive_integer])
    MASTER = DataField("master", MasterDeviceFields)
    URL = DataField("url", str, [is_not_empty_string])


class RoleFields(NestedDataFields):
    """Device role fields structure."""

    ID = DataField("id", int, [is_positive_integer])
    NAME = DataField("name", str, [is_not_empty_string])
    SLUG = DataField("slug", str, [is_not_empty_string])
    DISPLAY = DataField("display", str, [is_not_empty_string])
    DESCRIPTION = DataField("description", str)
    URL = DataField("url", str, [is_not_empty_string])


class DataFields:
    """Class to model the keys and values of the data dictionary on a Host"""

    # Custom fields
    AUTH_STATUS = DataField(
        "auth_status", str, [is_not_empty_string], FieldCategory.CUSTOM
    )
    BOOT_STATEMENT_SET = DataField(
        "boot_statement_set", bool, None, FieldCategory.CUSTOM
    )
    CONNECTION_ERROR = DataField(
        "connection_error", str, [is_not_empty_string], FieldCategory.CUSTOM
    )
    CURRENT_IMAGE = DataField(
        "current_image", str, [is_not_empty_string], FieldCategory.CUSTOM
    )
    DNS_IP = DataField("dns_ip", str, [is_not_empty_string], FieldCategory.CUSTOM)
    FLASH_SPACE_AVAILABLE = DataField(
        "flash_space_available", int, [is_positive_integer], FieldCategory.CUSTOM
    )
    HOSTNAME_VERIFIED = DataField("hostname_verified", bool, None, FieldCategory.CUSTOM)
    IMAGES_TO_DELETE = DataField("images_to_delete", list, None, FieldCategory.CUSTOM)
    INACTIVE = DataField("inactive", bool, None, FieldCategory.CUSTOM)
    IOS_VERSION = DataField(
        "ios_version", str, [is_not_empty_string], FieldCategory.CUSTOM
    )
    IS_AT_TARGET = DataField("is_at_target", bool, None, FieldCategory.CUSTOM)
    PING_STATUS = DataField(
        "ping_status", str, [is_not_empty_string], FieldCategory.CUSTOM
    )
    PRIMARY_IMAGE = DataField(
        "primary_image", str, [is_not_empty_string], FieldCategory.CUSTOM
    )
    PRIMARY_IMAGE_IN_FLASH = DataField(
        "primary_image_in_flash", bool, None, FieldCategory.CUSTOM
    )
    PRIMARY_IMAGE_MD5 = DataField(
        "primary_image_md5", str, [is_not_empty_string], FieldCategory.CUSTOM
    )
    PRIMARY_IMAGE_MD5_VERIFIED = DataField(
        "primary_image_md5_verified", bool, None, FieldCategory.CUSTOM
    )
    PRIMARY_IMAGE_SIZE = DataField(
        "primary_image_size", int, [is_positive_integer], FieldCategory.CUSTOM
    )
    RELOAD_SET = DataField("reload_set", bool, None, FieldCategory.CUSTOM)
    RELOAD_TIME = DataField(
        "reload_time", int, [is_positive_integer], FieldCategory.CUSTOM
    )
    SCP_ENABLED = DataField("scp_enabled", bool, None, FieldCategory.CUSTOM)
    SOLARWINDS_STATUS = DataField(
        "solarwinds_status", str, [is_not_empty_string], FieldCategory.CUSTOM
    )
    SSH_BULK_MODE = DataField("ssh_bulk_mode", bool, None, FieldCategory.CUSTOM)
    STACK_INFO = DataField("stack_info", StackInfoFields, None, FieldCategory.CUSTOM)
    SUPPORTS_SSH_BULK_MODE = DataField(
        "supports_ssh_bulk_mode", bool, None, FieldCategory.CUSTOM
    )

    # Netbox fields
    AIRFLOW = DataField("airflow", str)
    ASSET_TAG = DataField("asset_tag", str)
    CLUSTER = DataField("cluster", dict)
    COMMENTS = DataField("comments", str)
    CONFIG_CONTEXT = DataField("config_context", dict)
    CONFIG_TEMPLATE = DataField("config_template", dict)
    CONSOLE_PORT_COUNT = DataField("console_port_count", int)
    CONSOLE_SERVER_PORT_COUNT = DataField("console_server_port_count", int)
    CREATED = DataField("created", str, [is_not_empty_string])
    CUSTOM_FIELDS = DataField("custom_fields", dict)
    DESCRIPTION = DataField("description", str)
    DEVICE_BAY_COUNT = DataField("device_bay_count", int)
    DEVICE_TYPE = DataField("device_type", DeviceTypeFields)
    DISPLAY = DataField("display", str, [is_not_empty_string])
    FACE = DataField("face", str)
    FRONT_PORT_COUNT = DataField("front_port_count", int)
    ID = DataField("id", int, [is_positive_integer])
    INTERFACE_COUNT = DataField("interface_count", int, [is_positive_integer])
    INVENTORY_ITEM_COUNT = DataField("inventory_item_count", int)
    LAST_UPDATED = DataField("last_updated", str, [is_not_empty_string])
    LATITUDE = DataField("latitude", float)
    LOCAL_CONTEXT_DATA = DataField("local_context_data", dict)
    LOCATION = DataField("location", dict)
    LONGITUDE = DataField("longitude", float)
    MODULE_BAY_COUNT = DataField("module_bay_count", int)
    NAME = DataField("name", str, [is_not_empty_string])
    OOB_IP = DataField("oob_ip", dict)
    PARENT_DEVICE = DataField("parent_device", dict)
    PLATFORM = DataField("platform", PlatformFields)
    POSITION = DataField("position", int)
    POWER_OUTLET_COUNT = DataField("power_outlet_count", int)
    POWER_PORT_COUNT = DataField("power_port_count", int)
    PRIMARY_IP = DataField("primary_ip", dict)
    PRIMARY_IP4 = DataField("primary_ip4", dict)
    PRIMARY_IP6 = DataField("primary_ip6", dict)
    RACK = DataField("rack", dict)
    REAR_PORT_COUNT = DataField("rear_port_count", int)
    ROLE = DataField("role", RoleFields)
    SERIAL = DataField("serial", str)
    SITE = DataField("site", SiteFields)
    STATUS = DataField("status", StatusFields)
    TAGS = DataField("tags", list)
    TENANT = DataField("tenant", TenantFields)
    VC_POSITION = DataField("vc_position", int)
    VC_PRIORITY = DataField("vc_priority", int)
    VIRTUAL_CHASSIS = DataField("virtual_chassis", VirtualChassisFields)

    @classmethod
    def _get_fields_with_categories(cls, obj, prefix: str = ""):
        """Recursively get fields with their categories from a nested data structure.
        Returns tuples of (field_name, category).
        """
        if prefix:
            prefix += "__"

        fields = []
        for attr in dir(obj):
            val = getattr(obj, attr)
            if not isinstance(val, DataField):
                continue

            name = prefix + val.name
            category = val.field_category
            fields.append((name, category))

            if issubclass(val.t, NestedDataFields):
                fields.extend(cls._get_fields_with_categories(val.t, prefix=name))

        return fields

    @classmethod
    def get_fields(cls) -> list[str]:
        """Get all fields from the DataFields class and its nested classes.
        Sorted by category first, then alphabetically.
        """

        fields_with_categories = cls._get_fields_with_categories(cls)

        grouped: dict[FieldCategory, list[str]] = {}
        for category in FieldCategory:
            grouped[category] = []

        for name, category in fields_with_categories:
            grouped[category].append(name)

        for category in grouped:
            grouped[category].sort()

        result = []
        for category in FieldCategory:
            result.extend(grouped[category])

        return result


def get_required_host_vars(host: Host, required_vars: Sequence[DataField]) -> list[Any]:
    """Checks the host for the required variables and validates them.

    Args:
        host (Host): The host to check.
        required_vars (Sequence[DataField]): The sequence of DataFields attrs
        which are used as keys on host.data.

    Returns:
        list[Any]: A list with a boolean indicating if all required vars
        were found and valid, followed by the values of the required vars.
    """

    # Use first element as success indicator
    return_list: list[Any] = [True]
    missing: list[str] = []
    invalid: list[str] = []
    for var in required_vars:
        if var.name not in host.data:
            missing.append(var.name)
            return_list[0] = False
            continue
        value = host.data.get(var.name)
        if not var.validate(value):
            invalid.append(var.name)
            return_list[0] = False
            continue
        return_list.append(value)

    if missing:
        logging.error("%s not found for %s", ", ".join(missing), host)

    if invalid:
        logging.error("%s not valid for %s", ", ".join(invalid), host)

    return return_list


# YAML representer to turn DataField objects into plain strings
def datafield_representer(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", data.name)


yaml.add_representer(DataField, datafield_representer)
