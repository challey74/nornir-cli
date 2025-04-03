"""Singleton class for storing environment variables and configuring logging."""

from datetime import datetime
from typing import Optional

import os
import logging

from dotenv import load_dotenv
from rich.logging import RichHandler

from classes.metadata import Metadata
from classes.env import Env


class Config:
    """Singleton class for storing environment variables and configuring logging."""

    _instance: Optional["Config"] = None
    _is_initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if Config._is_initialized:
            return

        Config._is_initialized = True

        load_dotenv()
        print("Loading environment variables")

        self.env = Env()

        self._configure_logging()

        def _temp_loader():
            raise ValueError("Nornir loader not set")

        self.inventory_folder = os.path.join(os.getcwd(), "inventory")
        self.reports_folder = os.path.join(os.getcwd(), "reports")
        self.scp_enabled = False
        self._nornir = None
        self.nornir_loader = _temp_loader
        self.metadata = Metadata()
        self.file_handler = None
        self.rich_handler = None

        if not os.path.exists(self.inventory_folder):
            os.mkdir(self.inventory_folder)
        if not os.path.exists(self.reports_folder):
            os.mkdir(self.reports_folder)

    @property
    def nornir(self):
        """Nornir instance"""
        if self._nornir is None:
            self._nornir = self.nornir_loader()
        return self._nornir

    @nornir.setter
    def nornir(self, value):
        self._nornir = value

    def has_nornir(self):
        """Check if nornir instance is set"""
        return self._nornir is not None

    def _configure_logging(self):
        if not os.path.isdir("logs"):
            os.mkdir("logs")

        current_date = datetime.now().strftime("%Y-%m-%d")
        log_file = ""

        log_file = f"logs/{current_date}.log"
        self.file_handler = logging.FileHandler(log_file, mode="a+")
        self.rich_handler = RichHandler()
        logging.basicConfig(
            level=logging.INFO,
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[
                self.file_handler,
                self.rich_handler,
            ],
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

        logging.info("Logs stored at %s", log_file)
