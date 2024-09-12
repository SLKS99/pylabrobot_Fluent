from __future__ import annotations

import logging
import re
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Tuple, Union

import grpc
from grpc import ServicerContext

from sila2.framework.abc.sila_error import SilaError
from sila2.framework.command.command import Command
from sila2.framework.defined_execution_error_node import DefinedExecutionErrorNode
from sila2.framework.errors.defined_execution_error import DefinedExecutionError
from sila2.framework.errors.invalid_metadata import InvalidMetadata
from sila2.framework.errors.undefined_execution_error import UndefinedExecutionError
from sila2.framework.errors.validation_error import ValidationError
from sila2.framework.fully_qualified_identifier import FullyQualifiedIdentifier
from sila2.framework.metadata import Metadata
from sila2.framework.property.property import Property
from sila2.framework.utils import FullyQualifiedIdentifierRegex, raise_as_rpc_error

if TYPE_CHECKING:
    from sila2.server.sila_server import SilaServer

logger = logging.getLogger(__name__)


def _find_allowed_defined_execution_errors(
    server: SilaServer,
    origin: Optional[Union[Command, Property]] = None,
    metadata_identifiers: Optional[Iterable[FullyQualifiedIdentifier]] = None,
) -> List[DefinedExecutionErrorNode]:
    allowed_errors = []
    if origin is not None:
        allowed_errors.extend(origin.defined_execution_errors)
    if metadata_identifiers is not None:
        for metadata_id in metadata_identifiers:
            allowed_errors.extend(server.children_by_fully_qualified_identifier[metadata_id].defined_execution_errors)
    return allowed_errors


def extract_metadata(
    context: grpc.ServicerContext, server: SilaServer, origin: Union[Property, Command]
) -> Dict[FullyQualifiedIdentifier, Any]:
    metadata = {}
    for entry in context.invocation_metadata():
        key: str = entry.key
        if re.fullmatch(
            f"sila/{FullyQualifiedIdentifierRegex.MetadataIdentifier}/bin", key.replace("-", "/"), flags=re.IGNORECASE
        ):
            key = key[5:-4].replace("-", "/")

            try:
                meta: Metadata = server.children_by_fully_qualified_identifier[FullyQualifiedIdentifier(key)]
            except KeyError:
                raise_as_rpc_error(UndefinedExecutionError(KeyError(f"Server has no metadata {key}")), context)

            try:
                value = meta.to_native_type(entry.value)
            except Exception as ex:
                raise_as_rpc_error(InvalidMetadata(f"Failed to deserialize metadata value for {key!r}: {ex}"), context)

            raw_affected_calls = getattr(
                server.feature_servicers[meta.parent_feature._identifier].implementation,
                f"get_calls_affected_by_{meta._identifier}",
            )()
            affected_calls = [
                FullyQualifiedIdentifier(call) if isinstance(call, str) else call.fully_qualified_identifier
                for call in raw_affected_calls
            ]
            if (
                origin.fully_qualified_identifier not in affected_calls
                and origin.parent_feature.fully_qualified_identifier not in affected_calls
            ):
                logger.warning(
                    f"Metadata ignored because call should not be affected: "
                    f"{str(meta.fully_qualified_identifier)} with value {value}"
                )
                continue

            metadata[meta.fully_qualified_identifier] = value

        else:
            logger.debug(f"Found non-SiLA metadata {key!r} with value {entry.value!r}")
    return metadata


def unpack_parameters(command: Command, request, context: ServicerContext) -> Tuple[Any, ...]:
    try:
        return command.parameters.to_native_type(request)
    except ValidationError as val_err:
        raise_as_rpc_error(val_err, context)


@contextmanager
def raises_rpc_errors(
    context: ServicerContext,
    allowed_defined_execution_errors: Optional[Iterable[DefinedExecutionErrorNode]] = None,
):
    try:
        yield
    except Exception as ex:
        if not isinstance(ex, SilaError):
            raise_as_rpc_error(UndefinedExecutionError(ex), context)

        allowed_error_identifiers = [err.fully_qualified_identifier for err in allowed_defined_execution_errors]
        if isinstance(ex, DefinedExecutionError) and ex.fully_qualified_identifier not in allowed_error_identifiers:
            raise_as_rpc_error(UndefinedExecutionError(ex), context)

        raise_as_rpc_error(ex, context)
