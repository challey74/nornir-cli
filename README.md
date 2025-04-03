# CLI for Running Nornir

A command-line interface for network automation using [Nornir](https://github.com/nornir-automation/nornir) on Cisco devices.

## Disclaimer

This project is released as public source with the [Unlicense](https://unlicense.org/). No contributions will be accepted, no issues can be opened, and no pull requests will be reviewed. This code is provided as-is with no support or warranty.

## Overview

Nornir CLI uses the Nornir automation framework for network operations on Cisco devices. It provides a command-line interface built with Typer. Inventory can be provided with the default Nornir structure or via Netbox (see Inventory Management).

## Installation

```bash
# Clone the repository
git clone https://github.com/challey74/nornir-cli.git
cd nornir-cli

# Install dependencies with pip
pip install -r requirements.txt

# Or install with uv
uv sync
```

## Usage

### Shell Mode

The primary way to interact with Nornir CLI is through its interactive shell:

```bash
python src/cli.py shell
```

### Inventory Management

#### Loading Local Inventory

```
# In shell mode
get-inventory --folder-path inventory/my-inventory
```

Local inventory requires a default [Nornir inventory](https://nornir.readthedocs.io/en/latest/tutorial/inventory.html):

- `hosts.yaml`: Device definitions
- `groups.yaml`: Group configurations
- `defaults.yaml`: Default parameters
- Optional `metadata.yaml`: Inventory metadata (file specific to this project)

### NetBox Integration

The CLI provides NetBox integration for retrieving inventory through the `get-inventory` command:

```bash
# In shell mode
get-inventory --<api-parameter> <value>
```

List values can be passed as a comma separated string:

```bash
get-inventory --name--ic host1,host2,...
```

This command implements parameters from the NetBox REST API's `/dcim/devices` endpoint. For the complete list of available options, refer to the [NetBox API documentation](https://demo.netbox.dev/api/schema/swagger-ui/)

#### Filtering Inventory

Once inventory is loaded, it can be filtered:

Using the `filter-hosts` command with specific options for each field:

```
# Filter by platform
filter-hosts --filter-platform ios
```

Default behavior is to include hosts that match at least on filter. To inverse this to remove hosts that match any filter, use the `--exclude` flag.

## Key Components

### Configuration Singleton

The `Config` class implements a singleton pattern to manage the application state:

```python
from classes.config import Config

# Access the Config singleton
CONFIG = Config()
```

The Config singleton maintains:

- Environment variables via the `env` attribute
- Nornir instance access through the `nornir` property
- Logging configuration
- Path management for inventory and reports folders

### Environment Variables

Environment variables are accessible via the `Env` class through `CONFIG.env.<var>`.

### Data Fields

The `DataFields` class standardizes data keys used for device attributes.
These keys are used to store data in the host.data dict and for generate args
for the filter-hosts function.

```python
class DataFields:
    PRIMARY_IMAGE = "primary_image"
    IOS_VERSION = "ios_version"
    STACK_INFO = "stack_info"
    # Additional fields...
```

A helper function of `get_required_host_vars` is provided to know if any value is None
as the first element returned will be False.

Usage:

```python
def set_switch_boot_statement(task: Task, force: bool = True):
    success, primary_image, current_image, stack_info = get_required_host_vars(
        task.host,
        [DataFields.PRIMARY_IMAGE, DataFields.CURRENT_IMAGE, DataFields.STACK_INFO],
    )
    if not success:
        return
```

## Development

### Architecture

- Modules in the `classes` directory are for classes used throughout the project like Config
- Modules in the `commands` directory are entry points for the CLI and handle interaction with the user
- Modules in the `tasks` directory handle the business logic for commands
- Modules in the `utils` directory are for non-command or task functions

## License

This project is released under the [Unlicense](https://unlicense.org/) and is public domain.
