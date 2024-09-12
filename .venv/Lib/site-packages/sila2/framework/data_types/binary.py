from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Optional
from uuid import UUID

from sila2.framework.abc.binary_transfer_handler import BinaryTransferHandler
from sila2.framework.abc.data_type import DataType
from sila2.framework.abc.named_data_node import NamedDataNode
from sila2.framework.command.intermediate_response import IntermediateResponse
from sila2.framework.command.parameter import Parameter
from sila2.framework.command.response import Response
from sila2.framework.pb2 import SiLAFramework_pb2
from sila2.framework.pb2.SiLAFramework_pb2 import Binary as SilaBinary
from sila2.framework.property.property import Property

if TYPE_CHECKING:
    from sila2.client import ClientMetadataInstance
    from sila2.framework.feature import Feature


class Binary(DataType[SilaBinary, bytes]):
    message_type = SiLAFramework_pb2.Binary
    MAX_SIZE = 2 * 1024**2

    def __init__(self, parent_feature: Optional[Feature] = None):
        self.parent_feature = parent_feature

    def to_native_type(self, message: SilaBinary, toplevel_named_data_node: Optional[NamedDataNode] = None) -> bytes:
        if message.HasField("value"):
            return message.value

        if not message.HasField("binaryTransferUUID"):
            raise ValueError("Binary message has neither value, nor binaryTransferUUID")

        if self.get_binary_transfer_handler() is None:
            raise NotImplementedError("Feature reference does not implement Binary Transfer")

        binary_uuid = UUID(message.binaryTransferUUID)
        if isinstance(toplevel_named_data_node, (Parameter, Property, Response, IntermediateResponse)):
            return self.get_binary_transfer_handler().to_native_type(binary_uuid, toplevel_named_data_node)

        raise ValueError(
            "Binary Transfer only applies to Properties, Command Parameters, Responses and Intermediate Responses"
        )

    def to_message(
        self,
        value: bytes,
        *,
        toplevel_named_data_node: Optional[NamedDataNode] = None,
        metadata: Optional[Iterable[ClientMetadataInstance]] = None,
    ) -> SilaBinary:
        if not isinstance(value, bytes):
            raise TypeError("Expected a bytes value")

        if len(value) <= self.MAX_SIZE:
            return SiLAFramework_pb2.Binary(value=value)

        if isinstance(toplevel_named_data_node, (Parameter, Property, Response, IntermediateResponse)):
            if self.get_binary_transfer_handler() is None:
                raise NotImplementedError("Feature reference does not implement Binary Transfer")
            return self.get_binary_transfer_handler().to_message(
                value, toplevel_named_data_node=toplevel_named_data_node, metadata=metadata
            )

        raise ValueError(
            "Binary Transfer only applies to Properties, Command Parameters, Responses and Intermediate Responses"
        )

    def get_binary_transfer_handler(self) -> Optional[BinaryTransferHandler]:
        if self.parent_feature is None:
            return None
        return self.parent_feature._binary_transfer_handler
