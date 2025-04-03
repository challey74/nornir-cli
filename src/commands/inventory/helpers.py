from inspect import Parameter, Signature, signature
from typing import Callable, Optional, Any

import logging

from rich import print  # pylint: disable=W0622
from rich.prompt import Confirm

import typer

from classes.config import Config
from utils.data_fields import DataFields, StackInfoFields
from tasks.nornir import remove_hosts

CONFIG = Config()


def show_inventory_name():
    """Show save name in inventory."""
    print(CONFIG.metadata.name)


def show_hosts(
    verbose: bool = typer.Option(
        False, is_flag=True, help="Show hosts in inventory with all data."
    ),
):
    """Show hosts in inventory."""

    hosts = CONFIG.nornir.inventory.hosts
    if verbose:
        for host in hosts.values():
            print(host.dict())
    else:
        for host in hosts:
            print(host)


def show_md5_verification(
    failed_only: bool = typer.Option(
        False, is_flag=True, help="Show only failed md5 verifications."
    ),
    successful_only: bool = typer.Option(
        False, is_flag=True, help="Show only successful md5 verifications."
    ),
):
    hosts = CONFIG.nornir.inventory.hosts

    if failed_only:
        print("Failed MD5 Verification:")
        for hostname, host in hosts.items():
            if host.data.get(DataFields.PRIMARY_IMAGE_MD5_VERIFIED) is False:
                print(hostname)

    elif successful_only:
        print("Successful MD5 Verification:")
        for hostname, host in hosts.items():
            if host.data.get(DataFields.PRIMARY_IMAGE_MD5_VERIFIED) is True:
                print(hostname)

    else:
        print("MD5 Verification:")
        for hostname, host in hosts.items():
            print(f"{hostname}: {host.data.get(DataFields.PRIMARY_IMAGE_MD5_VERIFIED)}")


def show_groups(
    verbose: bool = typer.Option(
        False, is_flag=True, help="Show groups in inventory with all data."
    ),
):
    """Show groups in inventory."""

    groups = CONFIG.nornir.inventory.groups
    if verbose:
        print(groups)
    else:
        for group in groups:
            print(group)


def show_defaults(
    show_password: bool = typer.Option(
        False, is_flag=True, help="Show password in defaults."
    ),
):
    """Show defaults in inventory."""

    defaults = CONFIG.nornir.inventory.defaults.dict()
    if show_password:
        print(defaults)
    else:
        defaults["password"] = "********"
        print(defaults)


def show_options():
    """Show options in inventory."""

    options = CONFIG.nornir.inventory.options
    print(options)


def _generate_field_wrapper(
    help_text: str,
    flags: bool = True,
    include_filter_args: bool = True,
    include_regular_args: bool = True,
) -> Callable:
    # Collect and sort fields alphabetically
    all_fields = sorted(
        [field for field in dir(DataFields) if not field.startswith("_")]
    )
    all_fields.extend(
        sorted([field for field in dir(StackInfoFields) if not field.startswith("_")])
    )

    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(**kwargs)

        params = [
            p
            for p in list(signature(func).parameters.values())
            if p.name not in ["kwargs", "args"]
        ]

        if include_regular_args:
            # Add all show parameters first
            for field in all_fields:
                field = field.lower()
                if flags:
                    setattr(
                        wrapper,
                        field,
                        typer.Option(
                            False,
                            is_flag=True,
                            help=f"{help_text} {field}",
                            rich_help_panel=help_text.title(),
                        ),
                    )
                    params.append(
                        Parameter(
                            field,
                            Parameter.KEYWORD_ONLY,
                            default=False,
                            annotation=bool,
                        )
                    )
                else:
                    setattr(
                        wrapper,
                        field,
                        typer.Option(
                            "",
                            help=f"{help_text} {field} values",
                            rich_help_panel=help_text.title(),
                        ),
                    )
                    params.append(
                        Parameter(
                            field,
                            Parameter.KEYWORD_ONLY,
                            default="",
                            annotation=str,
                        )
                    )

        if include_filter_args:
            # Then add all filter parameters
            for field in all_fields:
                field = field.lower()
                setattr(
                    wrapper,
                    f"filter_{field}",
                    typer.Option(
                        None,
                        help=f"Filter {field} by comma-separated values",
                        rich_help_panel="Filter",
                    ),
                )
                params.append(
                    Parameter(
                        f"filter_{field}",
                        Parameter.KEYWORD_ONLY,
                        default=None,
                        annotation=Optional[str],
                    )
                )

        wrapper.__signature__ = Signature(params)
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator


def _get_host_data(host, field_name, default="NOT PRESENT"):
    if field_name.upper() in StackInfoFields.__dict__:
        return host.data.get(DataFields.STACK_INFO, {}).get(field_name, default)
    return host.data.get(field_name, default)


def _cast_value(value: str, cast_type: Any) -> Any:
    match cast_type.lower():
        case "int":
            try:
                return int(value)
            except ValueError:
                raise ValueError(f"Invalid value for int: {value}. Must be an integer.")
        case "bool":
            if value.lower() == "true":
                return True
            elif value.lower() == "false":
                return False
            raise ValueError(f"Invalid value for bool: {value}. Must be True or False.")
        case "none":
            return None
        case _:
            raise ValueError(
                f"Invalid cast type: {cast_type}. Must be int, bool, or None. Default is str."
            )


def _filter_hosts(hosts, filter_args):
    for hostname, host in hosts.items():
        matches_filters = True
        for field, filter_values in filter_args.items():
            if not filter_values:
                continue

            host_value = _get_host_data(host, field, None)
            if host_value not in filter_values:
                matches_filters = False
                break

        if not matches_filters:
            continue

        yield hostname, host


def _get_filter_args(kwargs):
    filter_args = {
        field.replace("filter_", ""): [
            _cast_value(v.split(":")[1], v.split(":")[0]) if ":" in v else v
            for v in values.replace(" ", "").split(",")
        ]
        for field, values in kwargs.items()
        if field.startswith("filter_") and values
    }
    return filter_args


def _get_reg_and_filter_args(kwargs):
    regular_args = [k for k, v in kwargs.items() if not k.startswith("filter_") and v]
    return regular_args, _get_filter_args(kwargs)


@_generate_field_wrapper(help_text="Show")
def show_host_data(
    count_only: bool = typer.Option(
        False, is_flag=True, help="Show count of hosts that match filters only."
    ),
    exclude: bool = typer.Option(
        False,
        is_flag=True,
        help="Exclude hosts that match any filters instead of including",
    ),
    **kwargs,
):
    """Show hosts in inventory with specific data fields
    and/or filter hosts by matching data fields."""
    hosts = CONFIG.nornir.inventory.hosts

    # Separate show flags from filter args
    show_specific_fields, filter_args = _get_reg_and_filter_args(kwargs)

    if exclude:
        matches = set(hostname for hostname, _ in _filter_hosts(hosts, filter_args))
        if not count_only:
            for hostname, host in hosts.items():
                if hostname in matches:
                    continue

                print(f"{hostname}:")
                if not show_specific_fields:
                    for field_name in kwargs:
                        if not field_name.startswith("filter_"):
                            print(
                                f"    {field_name}: {_get_host_data(host, field_name)}"
                            )
                    continue

                for field_name in show_specific_fields:
                    print(f"    {field_name}: {_get_host_data(host, field_name)}")

        count = len(hosts) - len(matches)
        print(f"Total hosts: {count}")
        return

    count = 0
    if not count_only:
        for hostname, host in _filter_hosts(hosts, filter_args):
            print(f"{hostname}:")
            if not show_specific_fields:
                for field_name in kwargs:
                    if not field_name.startswith("filter_"):
                        print(f"    {field_name}: {_get_host_data(host, field_name)}")
                continue

            for field_name in show_specific_fields:
                print(f"    {field_name}: {_get_host_data(host, field_name)}")

            count += 1
    else:
        count = sum(1 for _ in _filter_hosts(hosts, filter_args))

    print(f"Total hosts: {count}")


@_generate_field_wrapper(help_text="Set", flags=False)
def set_host_data(**kwargs):
    """set value to hosts in inventory with specific data fields
    and/or filter hosts by matching data fields. Use `type:value` to specify type.
    use `None:None` to set value to None.
    Example: `set_host_data --filter-site=site1 --ios-version int:16"""
    hosts = CONFIG.nornir.inventory.hosts

    set_fields, filter_args = _get_reg_and_filter_args(kwargs)

    for hostname, host in _filter_hosts(hosts, filter_args):
        for field_name in set_fields:
            value = kwargs[field_name]
            if not value:
                continue

            if ":" in value and field_name != DataFields.RELOAD_TIME:
                cast_type, value = value.split(":")
                value = _cast_value(value, cast_type)

            host.data[field_name] = value


@_generate_field_wrapper(help_text="Filter", include_regular_args=False)
def filter_hosts(
    name_contains: Optional[str] = typer.Option(None),
    site_id: Optional[str] = typer.Option(None),
    exclude: bool = typer.Option(
        False,
        is_flag=True,
        help="Remove hosts that match filters instead of the default of keeping them.",
    ),
    **kwargs,
):
    """Filter hosts in inventory by matching data fields.
    Matches device if ANY of the values are met (OR based logic)"""
    hosts = CONFIG.nornir.inventory.hosts

    matches = []
    # Check if any filter values are provided
    for value in kwargs.values():
        if value:
            filter_args = _get_filter_args(kwargs)
            matches.extend(
                [hostname for hostname, host in _filter_hosts(hosts, filter_args)]
            )
            break

    if name_contains is not None:
        matches.extend(
            [
                hostname
                for hostname in hosts
                if any(name.strip() in hostname for name in name_contains.split(","))
            ]
        )

    if site_id is not None:
        site_ids = [int(site) for site in site_id.split(",")]
        matches.extend(
            [
                hostname
                for hostname, host in hosts.items()
                if host.data.get("site", {}).get("id") in site_ids
            ]
        )

    if not matches:
        logging.warning("No hosts match filters. No action taken.")
        return

    not_matches = [hostname for hostname in hosts if hostname not in matches]

    if not not_matches:
        logging.info("All hosts match filters. No action taken.")
        return

    to_remove = matches if exclude else not_matches

    print(
        (
            "Keeping hosts that [bold]"
            + ("[bright_red]DO NOT MATCH" if exclude else "[bright_green]MATCH")
            + "[/][/] any filters:"
        )
    )

    filters = []
    if name_contains:
        filters.append(f"name_contains: {name_contains}")
    if site_id:
        filters.append(f"site_id: {site_id}")
    if kwargs:
        filters.extend(
            [f"{field}: {values}" for field, values in kwargs.items() if values]
        )
    print("[yellow]" + "\n".join(filters))

    if Confirm.ask(f"Remove {len(to_remove)} hosts from inventory?"):
        remove_hosts(to_remove)
    else:
        print("No action taken.")


def show_metadata():
    """Show metadata in inventory."""

    print(CONFIG.metadata.print())
