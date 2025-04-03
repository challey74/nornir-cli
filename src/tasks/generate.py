from classes.config import Config
from utils.data_fields import DataFields

CONFIG = Config()


def generate_host_list():
    hosts = []
    for host in CONFIG.nornir.inventory.hosts.values():
        hosts.append(host.name)

    with open("host_list.txt", "w+", encoding="UTF-8") as f:
        f.write("\n".join(hosts))


def generate_upgrading_host_list():
    hosts = []
    for host in CONFIG.nornir.inventory.hosts.values():
        if host.get(DataFields.IS_AT_TARGET) is False:
            hosts.append(host.name)

    with open("upgrading_host_list.txt", "w+", encoding="UTF-8") as f:
        f.write("\n".join(hosts))
