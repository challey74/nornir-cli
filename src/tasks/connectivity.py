import logging
import subprocess

from nornir.core.task import Task, Result
from netmiko.exceptions import NetmikoAuthenticationException
from nornir_netmiko.tasks import netmiko_send_command

from utils.data_fields import DataFields


def check_ping(task: Task, timeout: int = 10, count: int = 3):
    host = task.host.hostname

    try:
        cmd = f"ping -c {count} -W {timeout} {host}"
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
        )
        success = result.returncode == 0

    except subprocess.SubprocessError:
        success = False

    task.host.data[DataFields.PING_STATUS] = success


def check_credentials(task: Task) -> Result:
    try:
        task.host.open_connection(
            connection="napalm",
            configuration=task.nornir.config,
        )
        task.host.data[DataFields.AUTH_STATUS] = True

        return Result(
            host=task.host,
            result=f"Successfully authenticated to {task.host.name}",
        )

    except NetmikoAuthenticationException as e:
        task.host.data[DataFields.AUTH_STATUS] = False
        return Result(
            host=task.host,
            result=f"Authentication failed for {task.host.name}: {str(e)}",
        )

    except Exception as e:
        logging.error(f"Error: {e}")
        logging.error(type(e))
        task.host.data[DataFields.CONNECTION_ERROR] = str(e)
        return Result(
            host=task.host,
            result=f"Error occurred while authenticating to {task.host.name}: {str(e)}",
        )

    finally:
        task.host.close_connections()


def kill_line_sessions(task: Task) -> Result:
    """Kill all line sessions except the current one"""

    current_line = task.run(
        task=netmiko_send_command,
        command_string="show users | include *",
        enable=True,
        read_timeout=300,
    ).result

    try:
        current_line_num = current_line.split()[0]
    except (IndexError, AttributeError):
        return Result(
            host=task.host,
            result="Could not determine current line number",
            failed=True,
        )

    show_users = task.run(
        task=netmiko_send_command,
        command_string="show users",
        enable=True,
        read_timeout=300,
    ).result

    lines = []
    for line in show_users.splitlines():
        try:
            line_num = line.split()[0]
            if line_num.isdigit() and line_num != current_line_num:
                lines.append(line_num)
        except IndexError:
            continue

    results = []
    for line in lines:
        clear_result = task.run(
            task=netmiko_send_command,
            command_string=f"clear line {line}",
            enable=True,
            read_timeout=300,
        ).result
        results.append(f"Line {line}: {clear_result}")

    return Result(
        host=task.host, result=f"Cleared {len(lines)} sessions:\n" + "\n".join(results)
    )
