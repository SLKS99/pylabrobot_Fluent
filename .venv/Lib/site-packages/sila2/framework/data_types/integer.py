from __future__ import annotations

import re
from typing import TYPE_CHECKING, Iterable, Optional

from sila2.framework.abc.data_type import DataType
from sila2.framework.abc.named_data_node import NamedDataNode
from sila2.framework.pb2 import SiLAFramework_pb2
from sila2.framework.pb2.SiLAFramework_pb2 import Integer as SilaInteger

if TYPE_CHECKING:
    from sila2.client import ClientMetadataInstance


class Integer(DataType[SilaInteger, int]):
    message_type = SiLAFramework_pb2.Integer

    def to_native_type(self, message: SilaInteger, toplevel_named_data_node: Optional[NamedDataNode] = None) -> int:
        return message.value

    def to_message(
        self,
        value: int,
        *,
        toplevel_named_data_node: Optional[NamedDataNode] = None,
        metadata: Optional[Iterable[ClientMetadataInstance]] = None,
    ) -> SilaInteger:
        return SiLAFramework_pb2.Integer(value=value)

    @staticmethod
    def from_string(value: str) -> int:
        if not re.fullmatch("[-+]?[0-9]+", value):
            raise ValueError(f"Cannot parse as integer: '{value}'")
        return int(value)
