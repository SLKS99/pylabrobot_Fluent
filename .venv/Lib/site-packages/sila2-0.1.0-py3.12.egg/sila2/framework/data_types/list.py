from __future__ import annotations

from typing import TYPE_CHECKING, Any
from typing import List as TypingList
from typing import Optional

from google.protobuf.internal.containers import RepeatedCompositeFieldContainer

from sila2.framework.abc.data_type import DataType
from sila2.framework.abc.named_data_node import NamedDataNode
from sila2.framework.utils import xpath_sila

if TYPE_CHECKING:
    from sila2.framework.feature import Feature


class List(DataType):
    element_type: DataType

    def __init__(self, fdl_node, parent_feature: Feature, parent_namespace):
        self.element_type = DataType.from_fdl_node(
            xpath_sila(fdl_node, "sila:DataType")[0], parent_feature, parent_namespace
        )
        self.native_type = TypingList[self.element_type.native_type]
        self.message_type = TypingList[self.element_type.message_type]  # repeated fields are no messages

    def to_native_type(
        self, message: RepeatedCompositeFieldContainer, toplevel_named_data_node: Optional[NamedDataNode] = None
    ) -> Any:
        return [
            self.element_type.to_native_type(item, toplevel_named_data_node=toplevel_named_data_node)
            for item in message
        ]

    def to_message(self, items: TypingList, toplevel_named_data_node: Optional[NamedDataNode] = None) -> TypingList:
        return [self.element_type.to_message(item, toplevel_named_data_node=toplevel_named_data_node) for item in items]
