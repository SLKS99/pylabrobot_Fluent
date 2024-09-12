from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Optional

from sila2.framework.abc.data_type import DataType
from sila2.framework.abc.named_data_node import NamedDataNode
from sila2.framework.pb2 import SiLAFramework_pb2
from sila2.framework.pb2.SiLAFramework_pb2 import String as SilaString

if TYPE_CHECKING:
    from sila2.client import ClientMetadataInstance


class String(DataType[SilaString, str]):
    message_type = SiLAFramework_pb2.String

    def to_native_type(self, message: SilaString, toplevel_named_data_node: Optional[NamedDataNode] = None) -> str:
        return message.value

    def to_message(
        self,
        value: str,
        *,
        toplevel_named_data_node: Optional[NamedDataNode] = None,
        metadata: Optional[Iterable[ClientMetadataInstance]] = None,
    ) -> SilaString:
        if not isinstance(value, str):
            raise TypeError("Expected a str value")

        max_length = 2**21
        if len(value) > max_length:
            raise ValueError(f"String too long ({len(value)}, allowed: 2^21 characters)")
        return SiLAFramework_pb2.String(value=value)

    @staticmethod
    def from_string(value: str) -> str:
        return value
