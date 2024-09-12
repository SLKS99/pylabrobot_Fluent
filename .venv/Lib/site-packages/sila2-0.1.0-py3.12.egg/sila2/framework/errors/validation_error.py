from __future__ import annotations

from typing import TYPE_CHECKING

from sila2.framework.abc.sila_error import SilaError
from sila2.framework.command.parameter import Parameter
from sila2.framework.fully_qualified_identifier import FullyQualifiedIdentifier

if TYPE_CHECKING:
    from sila2.client.sila_client import SilaClient
    from sila2.pb2_stubs.SiLAFramework_pb2 import SiLAError
    from sila2.pb2_stubs.SiLAFramework_pb2 import ValidationError as SilaValidationError


class ValidationError(SilaError):
    parameterfully_qualified_identifier: FullyQualifiedIdentifier
    message: str

    def __init__(self, parameter: Parameter, message: str):
        self.parameterfully_qualified_identifier = parameter.fully_qualified_identifier
        self.message = message
        super().__init__(
            f"Constraint validation failed for parameter {self.parameterfully_qualified_identifier}: {message}"
        )

    def to_message(self) -> SiLAError:
        return self.pb2_module.SiLAError(
            validationError=self.pb2_module.ValidationError(
                parameter=self.parameterfully_qualified_identifier, message=self.message
            )
        )

    @classmethod
    def from_message(cls, message: SilaValidationError, client: SilaClient) -> ValidationError:
        return cls(
            client._children_by_fully_qualified_identifier[FullyQualifiedIdentifier(message.parameter)], message.message
        )
