import warnings
from typing import Dict
from uuid import UUID

from zeroconf import ServiceBrowser, ServiceInfo, ServiceListener, Zeroconf

from sila2.client.sila_client import SilaClient


class SilaServiceListener(ServiceListener):
    parent_browser: ServiceBrowser
    services: Dict[str, SilaClient]

    def __init__(self, parent_browser: ServiceBrowser):
        self.parent_browser = parent_browser
        self.services = {}

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        self.__add_client(info)

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        self.__add_client(info)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        if name in self.services:
            self.services.pop(name)

    def __add_client(self, service_info: ServiceInfo) -> None:
        service_name = service_info.name
        ip_address = service_info.parsed_addresses()[0]
        try:
            self.services[service_name] = SilaClient(ip_address, service_info.port)
        except Exception as ex:
            service_uuid = UUID(service_name.split(".")[0])
            warnings.warn(
                RuntimeWarning(
                    f"SiLA Server Discovery found a service with UUID {service_uuid} but failed to connect to it: "
                    f"{ex.__class__.__name__} - {ex}"
                )
            )
