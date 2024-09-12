from __future__ import annotations

from typing import TYPE_CHECKING

from sila2.framework.abc.data_type import DataType
from sila2.framework.abc.named_node import NamedNode
from sila2.framework.utils import xpath_sila

if TYPE_CHECKING:
    from sila2.framework.feature import Feature


class NamedDataNode(NamedNode):
    data_type: DataType

    def __init__(self, fdl_node, parent_feature: Feature, parent_namespace):
        super().__init__(fdl_node)
        self.data_type = DataType.from_fdl_node(
            xpath_sila(fdl_node, "sila:DataType")[0], parent_feature, parent_namespace
        )
