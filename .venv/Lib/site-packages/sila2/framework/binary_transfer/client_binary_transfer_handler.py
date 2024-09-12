from __future__ import annotations

from base64 import standard_b64decode
from typing import TYPE_CHECKING, Dict, Iterable, Optional
from uuid import UUID

import grpc

from sila2.client.utils import pack_metadata_for_grpc
from sila2.framework import SilaError
from sila2.framework.abc.binary_transfer_handler import BinaryTransferHandler
from sila2.framework.abc.binary_transfer_handler import grpc_module as binary_transfer_grpc_module
from sila2.framework.abc.binary_transfer_handler import pb2_module as binary_transfer_pb2_module
from sila2.framework.abc.named_data_node import NamedDataNode
from sila2.framework.binary_transfer.binary_transfer_error import (
    BinaryDownloadFailed,
    BinaryTransferError,
    BinaryUploadFailed,
)
from sila2.framework.command.parameter import Parameter
from sila2.framework.pb2 import SiLAFramework_pb2
from sila2.framework.utils import consume_generator

if TYPE_CHECKING:
    from sila2.client import ClientMetadataInstance, SilaClient
    from sila2.framework.pb2.SiLAFramework_pb2 import Binary as SilaBinary


class ClientBinaryTransferHandler(BinaryTransferHandler):
    _upload_stub: binary_transfer_grpc_module.BinaryUploadStub
    _download_stub: binary_transfer_grpc_module.BinaryDownloadStub
    _chunk_size = 1024**2  # 1 MB
    known_binaries: Dict[UUID, bytes]
    _parent_client: SilaClient

    def __init__(self, client: SilaClient):
        self._upload_stub = binary_transfer_grpc_module.BinaryUploadStub(client._channel)
        self._download_stub = binary_transfer_grpc_module.BinaryDownloadStub(client._channel)
        self.known_binaries = {}
        self._parent_client = client

    def to_native_type(self, binary_uuid: UUID, toplevel_named_data_node: Optional[NamedDataNode] = None) -> bytes:
        """Get binary data from a server response"""
        try:
            if binary_uuid in self.known_binaries:
                return self.known_binaries[binary_uuid]

            size: int = self._download_stub.GetBinaryInfo(
                binary_transfer_pb2_module.GetBinaryInfoRequest(binaryTransferUUID=str(binary_uuid))
            ).binarySize

            n_chunks = self.__compute_chunk_count(size)
            chunk_requests = (
                binary_transfer_pb2_module.GetChunkRequest(
                    binaryTransferUUID=str(binary_uuid),
                    offset=i * self._chunk_size,
                    length=self.__compute_chunk_length(size, i),
                )
                for i in range(n_chunks)
            )

            raw_result = bytearray(size)
            for chunk_response in self._download_stub.GetChunk(chunk_requests):
                raw_result[chunk_response.offset : chunk_response.offset + self._chunk_size] = chunk_response.payload

            result = bytes(raw_result)
            self.known_binaries[binary_uuid] = result

            # request deletion to free up server resources
            self._download_stub.DeleteBinary(
                binary_transfer_pb2_module.DeleteBinaryRequest(binaryTransferUUID=str(binary_uuid))
            )
            return result
        except Exception as ex:
            if BinaryTransferError.is_binary_transfer_error(ex):
                raise BinaryTransferError.from_rpc_error(ex)
            raise BinaryDownloadFailed(f"Exception during binary download: {ex}")

    def to_message(
        self,
        binary: bytes,
        *,
        toplevel_named_data_node: Parameter,
        metadata: Optional[Iterable[ClientMetadataInstance]] = None,
    ) -> SilaBinary:
        """Upload binary data to server"""
        n_chunks = self.__compute_chunk_count(len(binary))

        try:
            create_binary_response = self._upload_stub.CreateBinary(
                binary_transfer_pb2_module.CreateBinaryRequest(
                    binarySize=len(binary),
                    chunkCount=n_chunks,
                    parameterIdentifier=toplevel_named_data_node.fully_qualified_identifier,
                ),
                metadata=pack_metadata_for_grpc(metadata),
            )
        except Exception as ex:
            if isinstance(ex, grpc.RpcError) and ex.code() == grpc.StatusCode.ABORTED:
                details: bytes = standard_b64decode(ex.details())
                if details[0] == 0x08 or details[0] == 0x12 and details[-2:] == b"\x08\x01":
                    raise BinaryTransferError.from_rpc_error(ex)
                if details[0] in (0x1A, 0x22, 0x12):
                    raise SilaError.from_rpc_error(ex, self._parent_client)
            raise BinaryUploadFailed(f"Exception during binary upload: {ex}")

        try:
            binary_uuid = UUID(create_binary_response.binaryTransferUUID)

            chunk_requests = (
                binary_transfer_pb2_module.UploadChunkRequest(
                    binaryTransferUUID=str(binary_uuid),
                    chunkIndex=i,
                    payload=binary[i * self._chunk_size : (i + 1) * self._chunk_size],
                )
                for i in range(n_chunks)
            )

            chunk_responses = self._upload_stub.UploadChunk(chunk_requests)
            # UploadChunk can be implemented lazily so that a request is only processed once its response is requested
            consume_generator(chunk_responses)

            return SiLAFramework_pb2.Binary(binaryTransferUUID=str(binary_uuid))
        except Exception as ex:
            try:
                raise BinaryTransferError.from_rpc_error(ex)
            except:
                raise BinaryUploadFailed(f"Exception during binary upload: {ex}")

    def __compute_chunk_count(self, binary_size: int) -> int:
        return binary_size // self._chunk_size + (1 if binary_size % self._chunk_size != 0 else 0)

    def __compute_chunk_length(self, binary_size, chunk_index) -> int:
        return min(binary_size - chunk_index * self._chunk_size, self._chunk_size)
