from __future__ import annotations

from typing import TYPE_CHECKING

from zeroconf import ServiceInfo

if TYPE_CHECKING:
    from sila2.server.sila_server import SilaServer


class SilaServiceInfo(ServiceInfo):
    sila_server: SilaServer

    def __init__(self, server: SilaServer, address: str, port: int):
        super().__init__(
            type_="_sila._tcp.local.",
            name=f"{server.server_uuid}._sila._tcp.local.",
            parsed_addresses=[address],
            port=port,
            properties=dict(
                version=server.server_version,
                server_name=server.server_name,
                description=server.server_description,
            ),
        )
        self.sila_server = server
