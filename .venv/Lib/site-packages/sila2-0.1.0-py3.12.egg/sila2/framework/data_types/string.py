from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Type

from sila2.framework.abc.data_type import DataType
from sila2.framework.abc.named_data_node import NamedDataNode

if TYPE_CHECKING:
    from sila2.pb2_stubs import SiLAFramework_pb2
    from sila2.pb2_stubs.SiLAFramework_pb2 import String as SilaString


class String(DataType):
    native_type = str
    message_type: Type[SilaString]

    def __init__(self, silaframework_pb2_module: SiLAFramework_pb2):
        self.message_type = silaframework_pb2_module.String

    def to_native_type(self, message: SilaString, toplevel_named_data_node: Optional[NamedDataNode] = None) -> str:
        return message.value

    def to_message(self, value: str, toplevel_named_data_node: Optional[NamedDataNode] = None) -> SilaString:
        if not isinstance(value, str):
            raise TypeError("Expected a str value")

        max_length = 2 ** 21
        if len(value) > max_length:
            raise ValueError(f"String too long ({len(value)}, allowed: {max_length})")
        return self.message_type(value=value)

    @staticmethod
    def from_string(value: str) -> str:
        return value
