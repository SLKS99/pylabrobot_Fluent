from __future__ import annotations

import re
from typing import TYPE_CHECKING

from sila2.framework.abc.constraint import Constraint
from sila2.framework.utils import FullyQualifiedIdentifierRegex

if TYPE_CHECKING:
    from sila2.framework.abc.data_type import DataType
    from sila2.framework.feature import Feature


class FullyQualifiedIdentifier(Constraint):
    id_type: str

    def __init__(self, id_type: str):
        self.id_type = id_type

    def validate(self, value: str) -> bool:
        return bool(re.match(f"^{getattr(FullyQualifiedIdentifierRegex, self.id_type)}$", value))

    @classmethod
    def from_fdl_node(cls, fdl_node, parent_feature: Feature, base_type: DataType) -> FullyQualifiedIdentifier:
        return cls(fdl_node.text)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.id_type!r})"
