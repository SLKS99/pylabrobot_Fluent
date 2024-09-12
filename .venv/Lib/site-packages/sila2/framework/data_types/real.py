from __future__ import annotations

import re
from typing import TYPE_CHECKING, Iterable, Optional

from sila2.framework.abc.data_type import DataType
from sila2.framework.abc.named_data_node import NamedDataNode
from sila2.framework.pb2 import SiLAFramework_pb2
from sila2.framework.pb2.SiLAFramework_pb2 import Real as SilaReal

if TYPE_CHECKING:
    from sila2.client import ClientMetadataInstance


class Real(DataType[SilaReal, float]):
    message_type = SiLAFramework_pb2.Real

    def to_native_type(self, message: SilaReal, toplevel_named_data_node: Optional[NamedDataNode] = None) -> float:
        return message.value

    def to_message(
        self,
        value: float,
        *,
        toplevel_named_data_node: Optional[NamedDataNode] = None,
        metadata: Optional[Iterable[ClientMetadataInstance]] = None,
    ) -> SilaReal:
        if isinstance(value, int):
            value = float(value)  # get meaningful errors for impossible conversions, e.g. on overflows
        return SiLAFramework_pb2.Real(value=value)

    @staticmethod
    def from_string(value: str) -> float:
        # regex: https://www.w3.org/TR/xmlschema11-2/#nt-decimalRep
        if not re.fullmatch(r"([+-])?(\d+(\.\d*)?|\.\d+)", value):
            raise ValueError(f"Cannot parse as decimal: '{value}'")
        return float(value)
