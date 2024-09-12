from __future__ import annotations

from typing import TYPE_CHECKING

from sila2.framework.abc.named_node import NamedNode
from sila2.framework.fully_qualified_identifier import FullyQualifiedIdentifier

if TYPE_CHECKING:
    from sila2.framework.feature import Feature


class DefinedExecutionErrorNode(NamedNode):
    _parent_feature: Feature
    fully_qualified_identifier: FullyQualifiedIdentifier

    def __init__(self, fdl_node, parent_feature: Feature):
        super().__init__(fdl_node)
        self.fully_qualified_identifier = FullyQualifiedIdentifier(
            f"{parent_feature.fully_qualified_identifier}/DefinedExecutionError/{self._identifier}"
        )
