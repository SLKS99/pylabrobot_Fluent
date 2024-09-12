from __future__ import annotations

from typing import TYPE_CHECKING, Union

from sila2.framework.abc.sila_error import SilaError

if TYPE_CHECKING:
    from sila2.client.sila_client import SilaClient
    from sila2.pb2_stubs.SiLAFramework_pb2 import SiLAError
    from sila2.pb2_stubs.SiLAFramework_pb2 import UndefinedExecutionError as SilaUndefinedExecutionError


class UndefinedExecutionError(SilaError):
    message: str

    def __init__(self, message_or_exception: Union[str, Exception]):
        if isinstance(message_or_exception, Exception):
            self.message = f"{message_or_exception.__class__.__name__}: {message_or_exception}"
        else:
            self.message = message_or_exception
        super().__init__(self.message)

    def to_message(self) -> SiLAError:
        return self.pb2_module.SiLAError(
            undefinedExecutionError=self.pb2_module.UndefinedExecutionError(message=self.message)
        )

    @classmethod
    def from_message(cls, message: SilaUndefinedExecutionError, client: SilaClient) -> UndefinedExecutionError:
        return cls(message.message)
