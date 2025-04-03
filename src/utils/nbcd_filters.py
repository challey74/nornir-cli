"""
Custom filters for Nornir with Netbox inventory.
"""

import re
import logging

from nornir.core import Nornir

from classes.config import Config

CONFIG = Config()


def filter_hosts_from_set(nr: Nornir, filter_set):
    """Remove hosts that are not in the filter set."""

    to_del = []
    for hostname in nr.inventory.hosts:
        normalized = hostname.split(".")[
            0
        ].lower()  # All lower case, remove domain name if it exists.
        if normalized not in filter_set:
            to_del.append(hostname)
    for hostname in to_del:
        logging.debug(
            "%s: Removing from inventory. %s not in hosts filter.", hostname, normalized
        )
        del nr.inventory.hosts[hostname]


def domain_to_regex(domain: str) -> str:
    """Convert a domain to a regex pattern.
    Allows for a semi-colon and a single digit at the end of the domain."""
    escaped_domain = domain.replace(".", r"\.")

    pattern = rf"^.*\.{escaped_domain}(?::\d+)?$"

    return pattern


def filter_non_conforming_hostnames(nr: Nornir):
    """Remove hosts that do not conform to the hostname pattern."""

    if (domain := CONFIG.env.domain) is None:
        return

    logging.info("Removing non-conforming hostnames from inventory...")

    pattern = domain_to_regex(domain)

    to_del = []
    for hostname in nr.inventory.hosts:
        if not re.match(pattern, hostname):
            logging.warning(
                "%s: Removing from inventory."
                "Hostname does not end with .%s"
                "or :digit for stack.",
                hostname,
                domain,
            )
            to_del.append(hostname)
    for hostname in to_del:
        del nr.inventory.hosts[hostname]
        logging.info("%s: Removed from inventory.", hostname)


def filter_fix_stack_hostname(nr: Nornir):
    """Fix stack hostnames by removing the :n suffix and
    removing stack members that are not the master.

    Does not change the name of the object in the inventory,
    just the hostname attribute used by Netmiko."""

    to_del = []
    logging.info(
        "Identifying stack master hostname and removing stack members from inventory..."
    )
    for hostname, host in nr.inventory.hosts.items():
        if ":" in host.data["name"]:
            if not host.data["virtual_chassis"]:
                logging.error(
                    (
                        "%s: Suspected stack member (has : in hostname) does "
                        "not have virtual chassis assigned to it. "
                        "Removing from inventory."
                    ),
                    host,
                )
                to_del.append(hostname)
                continue
            if not host.data["virtual_chassis"]["master"]:
                logging.error(
                    (
                        "%s: Stack does not have master assigned to it, "
                        "which is required. Removing from inventory."
                    ),
                    host,
                )
                to_del.append(hostname)
                continue
            if host.data["id"] != host.data["virtual_chassis"]["master"]["id"]:
                logging.info("%s: Not master. Removing from inventory.", host)
                to_del.append(hostname)
                continue
            logging.info('%s is the master. Modifying hostname to remove ":n"', host)
            host.hostname = host.get("hostname").split(":")[0]

    for hostname in to_del:
        del nr.inventory.hosts[hostname]
