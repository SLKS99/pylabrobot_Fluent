from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable, List, Optional, Tuple, Union

import grpc
from google.protobuf.message import Message

from sila2.framework.abc.sila_error import SilaError
from sila2.framework.command.command import Command
from sila2.framework.errors.defined_execution_error import DefinedExecutionError
from sila2.framework.errors.sila_connection_error import SilaConnectionError
from sila2.framework.errors.undefined_execution_error import UndefinedExecutionError
from sila2.framework.fully_qualified_identifier import FullyQualifiedDefinedExecutionErrorIdentifier
from sila2.framework.property.property import Property

if TYPE_CHECKING:
    from sila2.client.client_metadata import ClientMetadataInstance
    from sila2.client.sila_client import SilaClient


def pack_metadata_for_grpc(metadata: Optional[Iterable[ClientMetadataInstance]]) -> Tuple[Tuple[str, bytes], ...]:
    # grpc metadata must be a n-tuple of 2-tuples (key/value pairs)
    if metadata is None:
        return ()

    return tuple(
        (meta_instance.metadata.to_grpc_header_key(), meta_instance.metadata.to_message(meta_instance.value))
        for meta_instance in metadata
    )


def get_allowed_errors(
    origin: Optional[Union[Command, Property]], metadata: Optional[Iterable[ClientMetadataInstance]]
) -> List[FullyQualifiedDefinedExecutionErrorIdentifier]:
    allowed_errors: List[FullyQualifiedDefinedExecutionErrorIdentifier] = []
    if origin is not None:
        allowed_errors.extend(e.fully_qualified_identifier for e in origin.defined_execution_errors)
    if metadata is not None:
        for meta_instance in metadata:
            allowed_errors.extend(e.fully_qualified_identifier for e in meta_instance.metadata.defined_execution_errors)
    return allowed_errors


def call_rpc_function(
    rpc_func: Any,
    parameter_message: Message,
    metadata: Optional[Iterable[ClientMetadataInstance]],
    client: SilaClient,
    origin: Optional[Union[Command, Property]],
):
    allowed_errors = get_allowed_errors(origin, metadata)
    grpc_metadata = pack_metadata_for_grpc(metadata)

    # call rpc function
    try:
        if hasattr(rpc_func, "with_call"):  # don't know when this is the case, but one of the two always seems to work
            response_msg, _ = rpc_func.with_call(parameter_message, metadata=grpc_metadata)
        else:
            response_msg = rpc_func(parameter_message, metadata=grpc_metadata)
        return response_msg
    except BaseException as ex:
        raise rpcerror_to_silaerror(ex, allowed_errors, client)


def rpcerror_to_silaerror(
    ex: BaseException, allowed_errors: List[FullyQualifiedDefinedExecutionErrorIdentifier], client: SilaClient
) -> Exception:
    if isinstance(ex, grpc.RpcError) and ex.code() == grpc.StatusCode.UNIMPLEMENTED:
        return UndefinedExecutionError(f"Method is not implemented by the server: {ex.details()}")

    if SilaError.is_sila_error(ex):
        sila_err = SilaError.from_rpc_error(ex, client=client)
        if isinstance(sila_err, DefinedExecutionError):
            # if defined execution error is not allowed for this call (-> server doesn't follow specs)
            if sila_err.fully_qualified_identifier not in allowed_errors:
                return UndefinedExecutionError(f"{sila_err.fully_qualified_identifier}: {sila_err.message}")
            # if client has an error class registered for this error
            if sila_err.fully_qualified_identifier in client._registered_defined_execution_error_classes:
                return client._registered_defined_execution_error_classes[sila_err.fully_qualified_identifier](
                    sila_err.message
                )
        return sila_err  # plain defined execution error, undefined execution error, validation or framework error
    return SilaConnectionError.from_exception(ex)  # server didn't send a SiLA error -> connection error


def is_channel_connected(channel: grpc.Channel, timeout: int = 1) -> bool:
    try:
        grpc.channel_ready_future(channel).result(timeout=timeout)
    except TimeoutError:
        return False
    return True
