from __future__ import annotations

import uuid
from datetime import timedelta
from typing import TYPE_CHECKING, Dict, Iterable, Optional
from uuid import UUID

from sila2.framework.abc.binary_transfer_handler import BinaryTransferHandler
from sila2.framework.abc.binary_transfer_handler import grpc_module as binary_transfer_grpc_module
from sila2.framework.abc.named_data_node import NamedDataNode
from sila2.framework.binary_transfer.binary_transfer_error import InvalidBinaryTransferUUID
from sila2.framework.binary_transfer.download_servicer import BinaryDownloadServicer
from sila2.framework.binary_transfer.upload_servicer import BinaryUploadServicer
from sila2.framework.pb2 import SiLAFramework_pb2

if TYPE_CHECKING:
    from sila2.client import ClientMetadataInstance
    from sila2.framework.pb2.SiLAFramework_pb2 import Binary as SilaBinary
    from sila2.server import SilaServer


class ServerBinaryTransferHandler(BinaryTransferHandler):
    upload_servicer: binary_transfer_grpc_module.BinaryUploadServicer
    download_servicer: binary_transfer_grpc_module.BinaryDownloadServicer
    known_binaries: Dict[UUID, bytes]

    def __init__(self, parent_server: SilaServer):
        self.parent_server = parent_server
        self.upload_servicer = BinaryUploadServicer(self)
        self.download_servicer = BinaryDownloadServicer(self)
        binary_transfer_grpc_module.add_BinaryUploadServicer_to_server(self.upload_servicer, parent_server.grpc_server)
        binary_transfer_grpc_module.add_BinaryDownloadServicer_to_server(
            self.download_servicer, parent_server.grpc_server
        )

        self.known_binaries = {}

    def to_native_type(self, binary_uuid: UUID, toplevel_named_data_node: Optional[NamedDataNode] = None) -> bytes:
        try:
            return self.known_binaries[binary_uuid]
        except KeyError:
            raise InvalidBinaryTransferUUID(f"Invalid binary transfer UUID: {binary_uuid}")

    def to_message(
        self,
        binary: bytes,
        *,
        toplevel_named_data_node: Optional[NamedDataNode] = None,
        metadata: Optional[Iterable[ClientMetadataInstance]] = None,
    ) -> SilaBinary:
        binary_uuid = uuid.uuid4()
        self.known_binaries[binary_uuid] = binary
        return SiLAFramework_pb2.Binary(binaryTransferUUID=str(binary_uuid))

    def get_default_lifetime(self) -> timedelta:
        return self.parent_server.default_binary_transfer_lifetime
