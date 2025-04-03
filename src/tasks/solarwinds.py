from functools import cache

from orionsdk import SwisClient

from classes.config import Config

CONFIG = Config()


@cache
def _get_swis_client():
    envs = {
        "SOLARWINDS_URL": CONFIG.env.solarwinds_url,
        "SOLARWINDS_USERNAME": CONFIG.env.solarwinds_username,
        "SOLARWINDS_PASSWORD": CONFIG.env.solarwinds_password,
    }

    missing_env_vars = []
    for k, v in envs.items():
        if not v:
            missing_env_vars.append(k)

    if missing_env_vars:
        raise ValueError(
            (
                "Failed to get SWIS Client.\n"
                f"No environment variable set for {', '.join(missing_env_vars)}"
            )
        )

    return SwisClient(
        CONFIG.env.solarwinds_url,
        CONFIG.env.solarwinds_username,
        CONFIG.env.solarwinds_password,
    )


def get_devices_status(names_list: list[str]) -> dict[str, bool]:
    client = _get_swis_client()

    formatted_list = ", ".join([f"'{name}'" for name in names_list])

    query = (
        f"SELECT "
        f"N.NodeID, "
        f"N.Caption as NodeName, "
        f"N.Status as NodeStatus "
        f"FROM Orion.Nodes N "
        f"WHERE N.Caption IN ({formatted_list})"
    )

    results = client.query(query)
    return {r["NodeName"].lower(): r["NodeStatus"] == 1 for r in results["results"]}
