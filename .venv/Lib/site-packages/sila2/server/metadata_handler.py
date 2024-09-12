from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Union

from sila2.framework import (
    Command,
    Feature,
    FullyQualifiedMetadataIdentifier,
    InvalidMetadata,
    Metadata,
    NoMetadataAllowed,
    ObservableProperty,
    Property,
    UnobservableProperty,
)
from sila2.framework.utils import FullyQualifiedIdentifierRegex

logger = logging.getLogger(__name__)


class ServerMetadataHandler:
    def __init__(
        self,
        required_metadata_by_call: Dict[Union[Command, Property], List[Metadata]],
    ):
        self.known_metadata: Dict[FullyQualifiedMetadataIdentifier, Metadata] = {}
        self.metadata_id_to_grpc_key: Dict[FullyQualifiedMetadataIdentifier, str] = {}
        self.metadata_grpc_key_to_id: Dict[str, FullyQualifiedMetadataIdentifier] = {}
        self.required_metadata_by_rpc_method: Dict[str, List[Metadata]] = {}

        for call, required_metadata in required_metadata_by_call.items():
            call_rpc_method = get_rpc_method_name(call)
            self.required_metadata_by_rpc_method[call_rpc_method] = required_metadata

            for meta in required_metadata:
                meta_id = meta.fully_qualified_identifier
                meta_grpc_key = metadata_identifier_to_grpc_metadata_key(meta_id)
                self.known_metadata[meta_id] = meta
                self.metadata_id_to_grpc_key[meta_id] = meta_grpc_key
                self.metadata_grpc_key_to_id[meta_grpc_key] = meta_id

    def extract_metadata(self, received_raw_metadata: Dict[str, bytes], rpc_method: str) -> Dict[Metadata, Any]:
        # check metadata targets SiLA Service
        if received_raw_metadata and is_silaservice_rpc_method(rpc_method):
            raise NoMetadataAllowed("Calls to the SiLA Service feature must not contain SiLA Client Metadata")

        # determine required metadata
        required_metadata = self.required_metadata_by_rpc_method[rpc_method]

        # parse required metadata
        parsed_metadata: Dict[Metadata, Any] = {}
        for meta in required_metadata:
            meta_key = self.metadata_id_to_grpc_key[meta.fully_qualified_identifier]

            # check missing metadata
            if meta_key not in received_raw_metadata:
                raise InvalidMetadata(f"Required SiLA Client Metadata is missing: {meta.fully_qualified_identifier}")

            # parse metadata
            try:
                parsed_message = meta.to_native_type(received_raw_metadata[meta_key])
                parsed_metadata[meta] = parsed_message
            except BaseException as ex:
                raise InvalidMetadata(f"Failed to deserialize metadata {meta.fully_qualified_identifier}: {ex}")

        return parsed_metadata


def is_sila_metadata_key(metadata_key: str) -> bool:
    return (
        re.fullmatch(
            f"sila/{FullyQualifiedIdentifierRegex.MetadataIdentifier}/bin",
            metadata_key.replace("-", "/"),
            flags=re.IGNORECASE,
        )
        is not None
    )


def metadata_key_to_fully_qualified_identifier(metadata_key: str) -> FullyQualifiedMetadataIdentifier:
    key = metadata_key[5:-4].replace("-", "/")
    return FullyQualifiedMetadataIdentifier(key)


def is_silaservice_rpc_method(rpc_method: str) -> bool:
    return rpc_method.startswith("/sila2.org.silastandard.core.silaservice.")


def metadata_identifier_to_grpc_metadata_key(metadata_identifier: FullyQualifiedMetadataIdentifier) -> str:
    return f"sila-{metadata_identifier.lower().replace('/', '-')}-bin"


def _get_rpc_method_prefix(feature: Feature) -> str:
    feature_major_version = feature._feature_version.split(".")[0]
    return ".".join(
        [
            "/sila2",
            feature._originator,
            feature._category,
            feature._identifier.lower(),
            "v" + feature_major_version,
            feature._identifier,
        ]
    )


def get_rpc_method_name(affected_call: Union[Command, Property]) -> str:
    prefix = _get_rpc_method_prefix(affected_call.parent_feature)

    if isinstance(affected_call, Command):
        return prefix + "/" + affected_call._identifier
    if isinstance(affected_call, UnobservableProperty):
        return prefix + "/Get_" + affected_call._identifier
    if isinstance(affected_call, ObservableProperty):
        return prefix + "/Get_" + affected_call._identifier
    raise TypeError(f"Expected a command or property, got {type(affected_call)}")  # pragma: no cover
