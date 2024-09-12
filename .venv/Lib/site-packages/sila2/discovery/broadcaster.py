from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional

from zeroconf import Zeroconf

from sila2.discovery.service_info import SilaServiceInfo

if TYPE_CHECKING:
    from sila2.server.sila_server import SilaServer


class SilaServiceBroadcaster:
    def __init__(self):
        self.zc = Zeroconf()
        self.registered_server_infos: Dict[SilaServer, SilaServiceInfo] = {}

    def register_server(self, server: SilaServer, address: str, port: int, ca: Optional[bytes] = None) -> None:
        service_info = SilaServiceInfo(server, address, port, ca)
        self.zc.register_service(service_info)
        self.registered_server_infos[server] = service_info

    def unregister_server(self, server: SilaServer) -> None:
        self.zc.unregister_service(self.registered_server_infos[server])
