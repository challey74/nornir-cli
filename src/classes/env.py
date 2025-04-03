import logging
import os
import sys


class Env:
    def __init__(self):
        self.domain = os.getenv("DOMAIN")
        self.image_folder = os.getenv("IMAGE_FOLDER")

        self.global_api_timeout = (
            int(os.getenv("GLOBAL_API_TIMEOUT"))
            if os.getenv("GLOBAL_API_TIMEOUT")
            else 180
        )

        self.tacacs_username = os.getenv("TACACS_USERNAME")
        self.tacacs_password = os.getenv("TACACS_PASSWORD")
        self.tacacs_v1_username = os.getenv("TACACS_V1_USERNAME")
        self.tacacs_v1_password = os.getenv("TACACS_V1_PASSWORD")

        self.netbox_url = os.getenv("NETBOX_URL")
        self.netbox_token = os.getenv("NETBOX_TOKEN")

        self.solarwinds_url = os.getenv("SOLARWINDS_URL")
        self.solarwinds_username = os.getenv("SOLARWINDS_USERNAME")
        self.solarwinds_password = os.getenv("SOLARWINDS_PASSWORD")

        self.ntp_vlan = os.getenv("NTP_VLAN")
        self.ntp_servers = (
            os.getenv("NTP_SERVERS").split(",") if os.getenv("NTP_SERVERS") else None
        )

        self.timezone = os.getenv("TIMEZONE")

    def __repr__(self):
        return str(self.__dict__)

    def __rich__(self):
        return self.__repr__()
