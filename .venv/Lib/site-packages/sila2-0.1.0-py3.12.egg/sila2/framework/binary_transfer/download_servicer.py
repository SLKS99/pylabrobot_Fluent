from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Iterable
from uuid import UUID

from grpc import ServicerContext

from sila2.framework.abc.binary_transfer_handler import grpc_module as binary_transfer_grpc_module
from sila2.framework.abc.binary_transfer_handler import pb2_module as binary_transfer_pb2_module
from sila2.framework.binary_transfer.binary_download_failed import BinaryDownloadFailed
from sila2.framework.binary_transfer.invalid_binary_transfer_uuid import InvalidBinaryTransferUUID
from sila2.framework.command.duration import Duration
from sila2.framework.utils import raise_as_rpc_error

if TYPE_CHECKING:
    from sila2.framework.binary_transfer.server_binary_transfer_handler import ServerBinaryTransferHandler


class BinaryDownloadServicer(binary_transfer_grpc_module.BinaryDownloadServicer):
    def __init__(self, parent_handler: ServerBinaryTransferHandler):
        self.parent_handler = parent_handler
        self._duration_field = Duration(binary_transfer_pb2_module.SiLAFramework__pb2)

    def GetBinaryInfo(self, request: binary_transfer_pb2_module.GetBinaryInfoRequest, context: ServicerContext):
        try:
            bin_id = UUID(request.binaryTransferUUID)

            if bin_id not in self.parent_handler.known_binaries:
                raise InvalidBinaryTransferUUID(f"Download of large binary failed: invalid UUID {bin_id}")

            return binary_transfer_pb2_module.GetBinaryInfoResponse(
                binarySize=len(self.parent_handler.known_binaries[bin_id]),
                lifetimeOfBinary=self._duration_field.to_message(timedelta(minutes=1)),
            )
        except InvalidBinaryTransferUUID as ex:
            raise_as_rpc_error(ex, context)
        except Exception as ex:
            raise_as_rpc_error(BinaryDownloadFailed(f"Download of large binary failed: {ex}"), context)

    def GetChunk(
        self, request_iterator: Iterable[binary_transfer_pb2_module.GetChunkRequest], context: ServicerContext
    ):
        try:
            for chunk_request in request_iterator:
                bin_id = UUID(chunk_request.binaryTransferUUID)

                if bin_id not in self.parent_handler.known_binaries:
                    raise InvalidBinaryTransferUUID(f"Download of large binary failed: invalid UUID {bin_id}")

                offset = chunk_request.offset
                length = chunk_request.length

                yield binary_transfer_pb2_module.GetChunkResponse(
                    binaryTransferUUID=str(bin_id),
                    offset=offset,
                    payload=self.parent_handler.known_binaries[bin_id][offset : offset + length],
                    lifetimeOfBinary=self._duration_field.to_message(timedelta(minutes=1)),
                )
        except InvalidBinaryTransferUUID as ex:
            raise_as_rpc_error(ex, context)
        except Exception as ex:
            raise_as_rpc_error(BinaryDownloadFailed(f"Download of large binary failed: {ex}"), context)

    def DeleteBinary(self, request: binary_transfer_pb2_module.DeleteBinaryRequest, context: ServicerContext):
        try:
            bin_id = UUID(request.binaryTransferUUID)

            if bin_id not in self.parent_handler.known_binaries:
                raise InvalidBinaryTransferUUID(f"Download of large binary failed: invalid UUID {bin_id}")

            self.parent_handler.known_binaries.pop(UUID(request.binaryTransferUUID))
            return binary_transfer_pb2_module.DeleteBinaryResponse()
        except InvalidBinaryTransferUUID as ex:
            raise_as_rpc_error(ex, context)
        except Exception as ex:
            raise_as_rpc_error(BinaryDownloadFailed(f"Deletion of large binary failed: {ex}"), context)
