from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from sila2.client.client_observable_command_instance import ClientObservableCommandInstance
from sila2.client.utils import call_rpc_function
from sila2.framework.command.command_confirmation import CommandConfirmation
from sila2.framework.command.observable_command import ObservableCommand

if TYPE_CHECKING:
    from sila2.client.client_feature import ClientFeature
    from sila2.pb2_stubs.SiLAFramework_pb2 import CommandConfirmation as SilaCommandConfirmation

ResultType = TypeVar("ResultType")
IntermediateType = TypeVar("IntermediateType")
T = TypeVar("T")


class ClientObservableCommand(Generic[ResultType, IntermediateType]):
    _parent_feature: ClientFeature
    _wrapped_command: ObservableCommand

    def __init__(self, parent_feature: ClientFeature, wrapped_command: ObservableCommand):
        self._parent_feature = parent_feature
        self._wrapped_command = wrapped_command

    def __call__(self, *args, **kwargs) -> ClientObservableCommandInstance:
        raw_metadata = kwargs.pop("metadata", None)
        param_msg = self._wrapped_command.parameters.to_message(*args, **kwargs)
        response_msg: SilaCommandConfirmation = call_rpc_function(
            getattr(self._parent_feature._grpc_stub, self._wrapped_command._identifier),
            param_msg,
            metadata=raw_metadata,
            client=self._parent_feature._parent_client,
            origin=self._wrapped_command,
        )
        confirmation = CommandConfirmation(self._parent_feature._pb2_module.SiLAFramework__pb2).to_native_type(
            response_msg
        )
        return ClientObservableCommandInstance(self, *confirmation)
