import tasks.workflows


def check_status():
    """Checks if device status is up in SolarWinds and ping is responsive"""

    tasks.workflows.check_status()


def handle_tacacs():
    """Checks and handles TACACS credentials"""

    tasks.workflows.check_and_handle_tacacs_credentials()
