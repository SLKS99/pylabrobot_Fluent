from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from google.protobuf.message import Message

from sila2.framework.abc.sila_error import SilaError
from sila2.framework.command.command import Command
from sila2.framework.errors.defined_execution_error import DefinedExecutionError
from sila2.framework.errors.sila_connection_error import SilaConnectionError
from sila2.framework.errors.undefined_execution_error import UndefinedExecutionError
from sila2.framework.fully_qualified_identifier import FullyQualifiedIdentifier
from sila2.framework.metadata import Metadata
from sila2.framework.property.property import Property

if TYPE_CHECKING:
    from sila2.client.client_metadata import ClientMetadata
    from sila2.client.sila_client import SilaClient


def dict_to_grpc_metadata(metadata: Dict[Metadata, Any]) -> Tuple[Tuple[str, bytes], ...]:
    if metadata is None:
        return tuple()

    metadata_tuple = []
    for meta, value in metadata.items():
        metadata_tuple.append((meta.to_grpc_header_key(), meta.to_message(value)))
    return tuple(metadata_tuple)


def call_rpc_function(
    rpc_func: Any,
    parameter_message: Message,
    metadata: Optional[Dict[Union[ClientMetadata, str], Any]],
    client: SilaClient,
    origin: Optional[Union[Command, Property]],
):
    allowed_errors: List[FullyQualifiedIdentifier] = []
    metadata_dict: Dict[Metadata, Any] = {}
    if origin is not None:
        allowed_errors.extend(e.fully_qualified_identifier for e in origin.defined_execution_errors)
    if metadata is not None:
        from sila2.client.client_metadata import ClientMetadata  # avoid cyclic imports

        for key, value in metadata.items():
            if isinstance(key, ClientMetadata):
                meta = key._wrapped_metadata
            else:
                meta: Metadata = client._children_by_fully_qualified_identifier[FullyQualifiedIdentifier(key)]
            allowed_errors.extend(e.fully_qualified_identifier for e in meta.defined_execution_errors)
            metadata_dict[meta] = value

    try:
        if hasattr(rpc_func, "with_call"):
            response_msg, _ = rpc_func.with_call(parameter_message, metadata=dict_to_grpc_metadata(metadata_dict))
        else:
            response_msg = rpc_func(parameter_message, metadata=dict_to_grpc_metadata(metadata_dict))
    except Exception as ex:
        if SilaError.is_sila_error(ex):
            sila_err = SilaError.from_rpc_error(ex, client=client)
            if isinstance(sila_err, DefinedExecutionError):
                if sila_err.fully_qualified_identifier not in allowed_errors:
                    raise UndefinedExecutionError(f"{sila_err.fully_qualified_identifier}: {sila_err.message}")
                if sila_err.fully_qualified_identifier in client._registered_defined_execution_error_classes:
                    raise client._registered_defined_execution_error_classes[sila_err.fully_qualified_identifier](
                        sila_err.message
                    )
            raise sila_err
        raise SilaConnectionError(ex)

    return response_msg
