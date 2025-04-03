from datetime import datetime

import yaml

from rich.prompt import Prompt


class Metadata:
    """Class for storing metadata for the inventory."""

    def __init__(self):
        self.name = None
        self.filter_parameters = None
        self.timestamp = None
        self.timestamp_formatted = None

    def set_metadata(
        self,
        name: str | None,
        filter_parameters: dict | None,
        timestamp: datetime | None,
    ):
        """Set metadata for the inventory."""

        self.name = name
        self.filter_parameters = filter_parameters
        self.timestamp = timestamp
        self.timestamp_formatted = (
            timestamp.strftime("%Y-%m-%d %H:%M:%S") if timestamp else None
        )

    def set_metadata_with_current_time(
        self, name: str | None, filter_parameters: dict | None
    ):
        """Set metadata with a now timestamp."""
        self.set_metadata(name, filter_parameters, datetime.now())

    def set_metadata_from_dict(self, metadata: dict):
        """Set metadata from a dictionary."""
        self.name = metadata.get("name")
        self.filter_parameters = metadata.get("filter_parameters")
        self.timestamp = metadata.get("timestamp")
        self.timestamp_formatted = metadata.get("timestamp_formatted")

    def set_metadata_from_file(self, filepath: str):
        """Set metadata from a yaml file."""
        with open(filepath, "r", encoding="utf-8") as file:
            metadata = yaml.safe_load(file)
            self.set_metadata_from_dict(metadata)

    def set_metadata_from_input(self, filter_parameters: dict | None):
        """Save metadata from user input."""
        result = Prompt.ask(
            "[bold white]Enter a name for the inventory (leave blank to use timestamp)"
        )
        self.set_metadata_with_current_time(
            result if result else None, filter_parameters
        )

    def save_metadata(self, filepath: str):
        """Save metadata to a yaml file."""
        with open(filepath, "w", encoding="utf-8") as file:
            yaml.dump(
                {
                    "name": self.name,
                    "filter_parameters": self.filter_parameters,
                    "timestamp": self.timestamp,
                    "timestamp_formatted": self.timestamp_formatted,
                },
                file,
            )

    def print(self):
        """Print metadata."""
        print(f"Name: {self.name}")
        print(f"Filter Parameters: {self.filter_parameters}")
        print(f"Time: {self.formatted_timestamp}")
