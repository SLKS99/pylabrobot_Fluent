from __future__ import annotations

from typing import TYPE_CHECKING, Generic, List, TypeVar

from sila2.client.utils import call_rpc_function
from sila2.framework.fully_qualified_identifier import FullyQualifiedIdentifier
from sila2.framework.metadata import Metadata

if TYPE_CHECKING:
    from sila2.client.client_feature import ClientFeature

T = TypeVar("T")


class ClientMetadata(Generic[T]):
    _parent_feature: ClientFeature
    _wrapped_metadata: Metadata
    fully_qualified_identifier: FullyQualifiedIdentifier

    def __init__(self, parent_feature: ClientFeature, wrapped_metadata: Metadata):
        self._parent_feature = parent_feature
        self._wrapped_metadata = wrapped_metadata
        self.fully_qualified_identifier = self._wrapped_metadata.fully_qualified_identifier

    def get_affected_calls(self) -> List[FullyQualifiedIdentifier]:
        param_msg = self._wrapped_metadata.get_affected_calls_parameters_message()

        response_msg = call_rpc_function(
            getattr(self._parent_feature._grpc_stub, f"Get_FCPAffectedByMetadata_{self._wrapped_metadata._identifier}"),
            param_msg,
            metadata=None,
            client=self._parent_feature._parent_client,
            origin=None,
        )

        return self._wrapped_metadata.to_affected_calls_list(response_msg)
