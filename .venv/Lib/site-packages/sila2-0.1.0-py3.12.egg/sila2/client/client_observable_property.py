from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Generic, Optional, TypeVar, Union

from sila2.client.subscription_stream import SubscriptionStream
from sila2.client.utils import call_rpc_function
from sila2.framework.property.observable_property import ObservableProperty

if TYPE_CHECKING:
    from sila2.client.client_feature import ClientFeature
    from sila2.client.client_metadata import ClientMetadata

T = TypeVar("T")


class ClientObservableProperty(Generic[T]):
    _parent_feature: ClientFeature
    _wrapped_property: ObservableProperty

    def __init__(self, parent_feature: ClientFeature, wrapped_property: ObservableProperty):
        self._parent_feature = parent_feature
        self._wrapped_property = wrapped_property

    def get(self, *, metadata: Optional[Dict[Union[ClientMetadata, str], Any]] = None) -> T:
        stream = self.subscribe(metadata=metadata)
        value = next(stream)
        stream.cancel()
        return value

    def subscribe(self, *, metadata: Optional[Dict[Union[ClientMetadata, str], Any]] = None) -> SubscriptionStream[T]:
        param_msg = self._wrapped_property.get_parameters_message()
        rpc_func = getattr(self._parent_feature._grpc_stub, f"Subscribe_{self._wrapped_property._identifier}")
        response_stream = call_rpc_function(
            rpc_func,
            param_msg,
            metadata=metadata,
            client=self._parent_feature._parent_client,
            origin=self._wrapped_property,
        )
        return SubscriptionStream(response_stream, self._wrapped_property.to_native_type)
