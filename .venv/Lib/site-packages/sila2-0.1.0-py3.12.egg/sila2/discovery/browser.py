import time
from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID

from zeroconf import ServiceBrowser, Zeroconf

from sila2.client.sila_client import SilaClient
from sila2.discovery.listener import SilaServiceListener


class SilaDiscoveryBrowser(ServiceBrowser):
    listener: SilaServiceListener
    clients: List[SilaClient]

    def __init__(self):
        self.listener = SilaServiceListener(self)
        super().__init__(Zeroconf(), "_sila._tcp.local.", self.listener)

    @property
    def clients(self) -> List[SilaClient]:
        return list(self.listener.services.values())

    def find_server(
        self, server_name: Optional[str] = None, server_uuid: Optional[Union[UUID, str]] = None, timeout: float = 0
    ) -> SilaClient:
        if timeout < 0:
            raise ValueError("Timeout must be non-negative")

        start_time = datetime.now()
        while timeout == 0 or (datetime.now() - start_time).total_seconds() < timeout:
            for client in self.clients:
                if server_name is not None and client.SiLAService.ServerName.get() != server_name:
                    continue
                if server_uuid is not None and client.SiLAService.ServerUUID.get() != str(server_uuid):
                    continue
                return client
            time.sleep(0.1)

        raise TimeoutError(f"No suitable SiLA server was found after {timeout} seconds")
