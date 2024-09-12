from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from zeroconf import ServiceInfo

from sila2.config import ENCODING
from sila2.framework.utils import resolve_host_to_ip_addresses

if TYPE_CHECKING:
    from sila2.server.sila_server import SilaServer


class SilaServiceInfo(ServiceInfo):
    sila_server: SilaServer

    def __init__(self, server: SilaServer, host: str, port: int, ca: Optional[bytes] = None):
        # UTF-8 encoded bytestring "key=value" must be <= 255 chars long -> truncate long entries
        properties = {
            "version": server.server_version.encode(ENCODING)[: 255 - len("version=")],
            "server_name": server.server_name.encode(ENCODING)[: 255 - len("server_name=")],
            "description": server.server_description.encode(ENCODING)[: 255 - len("description=")],
        }

        if ca is not None:
            properties.update({f"ca{i}": line for i, line in enumerate(ca.splitlines(keepends=False))})

        # ensure other devices don't try to connect via their localhost
        ip_addresses = resolve_host_to_ip_addresses(host)
        if len(ip_addresses) > 1 and "127.0.0.1" in ip_addresses:
            ip_addresses.remove("127.0.0.1")

        super().__init__(
            type_="_sila._tcp.local.",
            name=f"{server.server_uuid}._sila._tcp.local.",
            parsed_addresses=ip_addresses,
            port=port,
            properties=properties,
        )
        self.sila_server = server
