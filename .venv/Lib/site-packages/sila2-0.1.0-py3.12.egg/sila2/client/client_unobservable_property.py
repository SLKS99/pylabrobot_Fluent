from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Generic, Optional, TypeVar, Union

from sila2.client.utils import call_rpc_function
from sila2.framework.property.unobservable_property import UnobservableProperty

if TYPE_CHECKING:
    from sila2.client.client_feature import ClientFeature
    from sila2.client.client_metadata import ClientMetadata

T = TypeVar("T")


class ClientUnobservableProperty(Generic[T]):
    _parent_feature: ClientFeature
    _wrapped_property: UnobservableProperty

    def __init__(self, parent_feature: ClientFeature, wrapped_property: UnobservableProperty):
        self._parent_feature = parent_feature
        self._wrapped_property = wrapped_property

    def get(self, *, metadata: Optional[Dict[Union[ClientMetadata, str], Any]] = None) -> T:
        param_msg = self._wrapped_property.get_parameters_message()

        response_msg = call_rpc_function(
            getattr(self._parent_feature._grpc_stub, f"Get_{self._wrapped_property._identifier}"),
            param_msg,
            metadata=metadata,
            client=self._parent_feature._parent_client,
            origin=self._wrapped_property,
        )

        return self._wrapped_property.to_native_type(response_msg)
