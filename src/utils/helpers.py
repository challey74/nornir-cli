from collections import deque
from typing import Any

from classes.config import Config

CONFIG = Config()


def search_dict_for_key(dictionary: dict[str, Any], target_key: str):
    """Search a nested dictionary for a specific key.

    Args:
        dictionary (dict): The dictionary to search.
        target_key (str): The key to search for.

    Returns:
        The value of the target key if found, otherwise None.
    """

    queue = deque([(dictionary, [])])

    while queue:
        current_dict, path = queue.popleft()

        for key, value in current_dict.items():
            current_path = path + [key]

            if key == target_key:
                return value

            if isinstance(value, dict):
                queue.append((value, current_path))

    return None


def add_domain_if_missing(host: str) -> str:
    """Add the domain to a hostname if it is missing."""

    if f".{CONFIG.env.domain}" in host:
        return host

    return f"{host}.{CONFIG.env.domain}"


def clean_hostname(hostname: str) -> str:
    """Clean a hostname by making it lowercase and adding the domain if missing.
    Removes semi-colon and digit from stack hostnames"""

    return add_domain_if_missing(hostname.lower().split(":")[0])
