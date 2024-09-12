from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from sila2.client.utils import call_rpc_function
from sila2.framework.command.unobservable_command import UnobservableCommand

if TYPE_CHECKING:
    from sila2.client.client_feature import ClientFeature

T = TypeVar("T")


class ClientUnobservableCommand(Generic[T]):
    _parent_feature: ClientFeature
    _wrapped_command: UnobservableCommand

    def __init__(self, parent_feature: ClientFeature, wrapped_command: UnobservableCommand):
        self._parent_feature = parent_feature
        self._wrapped_command = wrapped_command

    def __call__(self, *args, **kwargs) -> T:
        raw_metadata = kwargs.pop("metadata", None)
        param_msg = self._wrapped_command.parameters.to_message(
            *args, **kwargs, toplevel_named_data_node=self._wrapped_command.parameters
        )
        response_msg = call_rpc_function(
            getattr(self._parent_feature._grpc_stub, self._wrapped_command._identifier),
            param_msg,
            metadata=raw_metadata,
            client=self._parent_feature._parent_client,
            origin=self._wrapped_command,
        )

        return self._wrapped_command.responses.to_native_type(response_msg)
