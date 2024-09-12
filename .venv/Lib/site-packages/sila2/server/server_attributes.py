import re
import sys
import uuid
from dataclasses import dataclass
from typing import Optional, Union

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from uuid import UUID

SERVER_TYPE_REGEX = "[A-Z][a-zA-Z0-9]*"
SERVER_VENDOR_URL_REGEX = "https?://.+"
SERVER_VERSION_REGEX = r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))?(_[_a-zA-Z0-9]+)?"


@dataclass
class ServerAttributes:
    server_name: str
    server_type: str
    server_description: str
    server_version: str
    server_vendor_url: str
    server_uuid: UUID = None

    @classmethod
    def create(
        cls,
        server_name: str,
        server_type: str,
        server_version: str,
        server_description: str,
        server_vendor_url: str,
        server_uuid: Optional[Union[UUID, str]],
    ) -> Self:
        attributes = cls(
            server_name=server_name,
            server_uuid=_parse_or_create_uuid(server_uuid),
            server_type=server_type,
            server_description=server_description,
            server_vendor_url=server_vendor_url,
            server_version=server_version,
        )
        attributes.validate()
        return attributes

    def validate(self) -> None:
        if len(self.server_name) >= 256:
            raise ValueError("Server name must be shorter than 256 characters")
        if not re.fullmatch(SERVER_TYPE_REGEX, self.server_type):
            raise ValueError(f"Server type must match regex '{SERVER_TYPE_REGEX}' (e.g. 'BarcodeScanner')")
        if not re.fullmatch(SERVER_VERSION_REGEX, self.server_version):
            raise ValueError("Server version has invalid format. Examples: '2.1', '0.1.3', '1.2.3_preview'")
        if not re.fullmatch(SERVER_VENDOR_URL_REGEX, self.server_vendor_url):
            raise ValueError("Server vendor url must start with 'https://' or 'http://'")


def _parse_or_create_uuid(server_uuid: Optional[Union[UUID, str]]) -> UUID:
    if server_uuid is None:
        return uuid.uuid4()
    if isinstance(server_uuid, UUID):
        return server_uuid
    return UUID(server_uuid)
