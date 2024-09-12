from __future__ import annotations

from typing import TYPE_CHECKING

from sila2.framework.abc.sila_error import SilaError
from sila2.framework.defined_execution_error_node import DefinedExecutionErrorNode
from sila2.framework.fully_qualified_identifier import FullyQualifiedIdentifier

if TYPE_CHECKING:
    from sila2.client.sila_client import SilaClient
    from sila2.pb2_stubs.SiLAFramework_pb2 import DefinedExecutionError as SilaDefinedExecutionError
    from sila2.pb2_stubs.SiLAFramework_pb2 import SiLAError


class DefinedExecutionError(SilaError):
    message: str
    identifier: str
    fully_qualified_identifier: FullyQualifiedIdentifier

    def __init__(self, error_node: DefinedExecutionErrorNode, message: str):
        self.message = message
        self.identifier = error_node._identifier
        self.fully_qualified_identifier = error_node.fully_qualified_identifier
        super().__init__(f"{error_node._identifier}: {message}")

    def to_message(self) -> SiLAError:
        return self.pb2_module.SiLAError(
            definedExecutionError=self.pb2_module.DefinedExecutionError(
                errorIdentifier=self.fully_qualified_identifier, message=self.message
            )
        )

    @classmethod
    def from_message(cls, message: SilaDefinedExecutionError, client: SilaClient) -> DefinedExecutionError:
        return cls(
            client._children_by_fully_qualified_identifier[FullyQualifiedIdentifier(message.errorIdentifier)],
            message.message,
        )
