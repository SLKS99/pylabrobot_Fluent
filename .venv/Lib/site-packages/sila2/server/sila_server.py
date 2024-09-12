from __future__ import annotations

import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from enum import IntEnum, auto
from typing import TYPE_CHECKING, Dict, List, Optional, Union
from uuid import UUID

import grpc

from sila2.discovery.broadcaster import SilaServiceBroadcaster
from sila2.framework.binary_transfer.server_binary_transfer_handler import ServerBinaryTransferHandler
from sila2.framework.command.command import Command
from sila2.framework.feature import Feature
from sila2.framework.fully_qualified_identifier import FullyQualifiedIdentifier, FullyQualifiedMetadataIdentifier
from sila2.framework.property.property import Property
from sila2.server.encryption import generate_self_signed_certificate
from sila2.server.feature_implementation_base import FeatureImplementationBase
from sila2.server.feature_implementation_servicer import FeatureImplementationServicer
from sila2.server.metadata_interceptor import MetadataInterceptor
from sila2.server.server_attributes import ServerAttributes

if TYPE_CHECKING:
    from sila2.framework.command.intermediate_response import IntermediateResponse
    from sila2.framework.command.parameter import Parameter
    from sila2.framework.command.response import Response
    from sila2.framework.data_types.data_type_definition import DataTypeDefinition
    from sila2.framework.defined_execution_error_node import DefinedExecutionErrorNode
    from sila2.framework.metadata import Metadata


logger = logging.getLogger(__name__)


class ServerState(IntEnum):
    NOT_STARTED = auto()
    RUNNING = auto()
    STOPPED = auto()


class SilaServer:
    generated_ca: Optional[bytes]
    """PEM-encoded certificate authority of self-signed certificate, if generated on server startup"""

    metadata_interceptors: List[MetadataInterceptor]
    """Registered metadata interceptors"""

    children_by_fully_qualified_identifier: Dict[
        FullyQualifiedIdentifier,
        Union[
            Feature,
            Command,
            Property,
            Parameter,
            Response,
            IntermediateResponse,
            DefinedExecutionErrorNode,
            DataTypeDefinition,
            Metadata,
        ],
    ]
    """All child elements, accessible by their fully qualified identifier"""

    def __init__(
        self,
        server_name: str,
        server_type: str,
        server_description: str,
        server_version: str,
        server_vendor_url: str,
        server_uuid: Optional[Union[str, UUID]] = None,
        max_grpc_workers: int = 100,
        max_child_task_workers: int = 100,
        default_binary_transfer_lifetime: timedelta = timedelta(minutes=1),
    ):
        """
        SiLA Server

        Parameters
        ----------
        server_name
            SiLA Server Name, max. 255 characters
        server_type
            SiLA Server Type, must start with a capital letter and can only contain letters (a-z, A-Z) and digits (0-9)
        server_description
            SiLA Server Description
        server_version
            SiLA Server Version, e.g. ``"1.2"``, ``"1.2.3"``, or ``"1.2.3_beta"``.

            Pattern: ``Major.Minor.Patch_Details``,
            where *Major*, *Minor* und *Patch* are numeric, *Details* is text (a-z, A-Z, 0-9, _).
            *Patch* and *Details* are optional.
        server_vendor_url
            SiLA Server Vendor URL: The product or vendor homepage, must start with ``"http://"`` or ``"https://"``
        server_uuid
            SiLA Server UUID. If given as a string, it must be formatted like ``"082bc5dc-18ae-4e17-b028-6115bbc6d21e"``
        max_grpc_workers
            Max. number of worker threads used by gRPC
        max_child_task_workers
            Max. number of worker threads used by the implementation
            (e.g. observable command instances, observable property subscriptions, ...)
        """
        self.attributes = ServerAttributes.create(
            server_name=server_name,
            server_uuid=server_uuid,
            server_type=server_type,
            server_description=server_description,
            server_vendor_url=server_vendor_url,
            server_version=server_version,
        )
        self.default_binary_transfer_lifetime = default_binary_transfer_lifetime

        # initialize server state
        self.features: Dict[str, Feature] = {}
        self.feature_servicers: Dict[str, FeatureImplementationServicer] = {}
        self.metadata_interceptors = []
        self.children_by_fully_qualified_identifier = {}
        self.generated_ca = None
        self.__state = ServerState.NOT_STARTED

        self.grpc_server = grpc.server(
            ThreadPoolExecutor(max_workers=max_grpc_workers, thread_name_prefix=f"grpc-executor-{self.server_uuid}")
        )
        self.binary_transfer_handler = ServerBinaryTransferHandler(self)

        self.child_task_executor = ThreadPoolExecutor(
            max_workers=max_child_task_workers, thread_name_prefix=f"child-task-executor-{self.server_uuid}"
        )
        self.__service_broadcaster = SilaServiceBroadcaster()

        self.__add_sila_service()

    def set_feature_implementation(self, feature: Feature, implementation: FeatureImplementationBase) -> None:
        """
        Set a feature implementation

        Parameters
        ----------
        feature
            Feature to implement
        implementation
            Feature implementation

        Raises
        ------
        RuntimeError
            If the server was already started, or another implementation of the feature already was set
        """
        if self.__state != ServerState.NOT_STARTED:
            raise RuntimeError("Can only add features before starting the server")
        if feature._identifier in self.feature_servicers:
            raise RuntimeError("Can only add one implementation per feature")

        servicer = self.__create_feature_implementation_servicer(feature, implementation)
        self.__add_servicer_to_server(servicer, self.grpc_server)
        self.feature_servicers[feature._identifier] = servicer

        feature._binary_transfer_handler = self.binary_transfer_handler

        self.features[feature._identifier] = feature
        self.children_by_fully_qualified_identifier[feature.fully_qualified_identifier] = feature
        self.children_by_fully_qualified_identifier.update(feature.children_by_fully_qualified_identifier)

    @staticmethod
    def __add_servicer_to_server(servicer: FeatureImplementationServicer, server: grpc.Server) -> None:
        feature = servicer.feature
        getattr(feature._grpc_module, f"add_{feature._identifier}Servicer_to_server")(servicer, server)

    def __create_feature_implementation_servicer(
        self, feature: Feature, implementation: FeatureImplementationBase
    ) -> FeatureImplementationServicer:
        class FeatureServicer(FeatureImplementationServicer, feature._servicer_cls):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.set_implementation(implementation)

        servicer: FeatureImplementationServicer = FeatureServicer(self, feature)
        return servicer

    def add_metadata_interceptor(self, interceptor: MetadataInterceptor):
        """
        Add an interceptor for SiLA Client Metadata handling

        Parameters
        ----------
        interceptor
            Interceptor to add

        Raises
        ------
        RuntimeError
            If the server is already running
        """
        if self.__state != ServerState.NOT_STARTED:
            raise RuntimeError("Can only metadata interceptors before server is started")
        self.metadata_interceptors.append(interceptor)

    def __collect_calls_affected_by_metadata(
        self,
    ) -> Dict[FullyQualifiedIdentifier, List[FullyQualifiedMetadataIdentifier]]:
        # like dict[feature/command/property-identifier, metadata-identifier]
        affected_calls: Dict[FullyQualifiedIdentifier, List[FullyQualifiedMetadataIdentifier]] = defaultdict(list)

        for servicer in self.feature_servicers.values():
            for metadata in servicer.feature.metadata_definitions.values():
                calls_affected_by_metadata = getattr(servicer, f"get_calls_affected_by_{metadata._identifier}")()
                for call in calls_affected_by_metadata:
                    if isinstance(call, FullyQualifiedIdentifier):
                        affected_call = call
                    else:
                        affected_call = call.fully_qualified_identifier
                    affected_calls[affected_call].append(metadata.fully_qualified_identifier)
        return affected_calls

    def start_insecure(self, address: str, port: int, enable_discovery: bool = True) -> None:
        """
        Start the server using unencrypted communication

        Parameters
        ----------
        address
            IP address or hostname where the server should run
        port
            Port where the server should run
        enable_discovery
            Whether to broadcast the server address for SiLA Server Discovery

        Warnings
        --------
        Using unencrypted communication violates the SiLA specification and should only be used for testing purposes

        Notes
        -----
        From the SiLA Specification:

            It is RECOMMENDED that all SiLA Servers have SiLA Server Discovery enabled by default, but all
            SiLA Devices MUST have SiLA Server Discovery enabled by default.
        """
        self.__start(address, port, insecure=True, enable_discovery=enable_discovery)

    def start(
        self,
        address: str,
        port: int,
        private_key: Optional[bytes] = None,
        cert_chain: Optional[bytes] = None,
        ca_for_discovery: Optional[bytes] = None,
        enable_discovery: bool = True,
    ):
        """
        Start the server using unencrypted communication

        When no encryption information is provided, a self-signed certificate is generated.
        Its PEM-encoded certificate authority is then stored in :py:attr:`sila2.server.SilaServer.generated_ca`.

        Parameters
        ----------
        address
            IP address or hostname where the server should run
        port
            Port where the server should run
        private_key
            PEM-encoded private key for encrypted communication
        cert_chain
            PEM-encoded certificate chain for encrypted communication
        ca_for_discovery
            PEM-encoded certificate of the certificate authority that  should be used in the SiLA Server Discovery
            (only useful if you manually provide an untrusted certificate)
        enable_discovery
            Whether to broadcast the server address for SiLA Server Discovery

        Notes
        -----
        From the SiLA Specification:

            It is RECOMMENDED that all SiLA Servers have SiLA Server Discovery enabled by default, but all
            SiLA Devices MUST have SiLA Server Discovery enabled by default.
        """
        self.__start(
            address,
            port,
            insecure=False,
            private_key=private_key,
            cert_chain=cert_chain,
            ca_for_discovery=ca_for_discovery,
            enable_discovery=enable_discovery,
        )

    def __start(
        self,
        address: str,
        port: int,
        *,
        insecure: bool,
        private_key: Optional[bytes] = None,
        cert_chain: Optional[bytes] = None,
        ca_for_discovery: Optional[bytes] = None,
        enable_discovery: bool = True,
    ):
        if self.__state != ServerState.NOT_STARTED:
            raise RuntimeError("Cannot start server twice")

        self.__add_port_to_grpc_server(
            address, ca_for_discovery, cert_chain, enable_discovery, insecure, port, private_key
        )
        self.grpc_server.start()

        # start implementations
        for servicer in self.feature_servicers.values():
            servicer.start()

        # start zeroconf broadcasting
        if enable_discovery:
            self.__start_zeroconf_broadcasting(address, port, ca_for_discovery)

        logger.info("Server started")
        self.__state = ServerState.RUNNING

    def __add_port_to_grpc_server(
        self,
        address: str,
        ca_for_discovery: Optional[bytes],
        cert_chain: Optional[bytes],
        enable_discovery: bool,
        insecure: bool,
        port: int,
        private_key: Optional[bytes],
    ):
        address_string = f"{address}:{port}"
        if insecure:
            logger.warning("Starting SiLA server without encryption. This violates the SiLA 2 specification.")
            self.grpc_server.add_insecure_port(address_string)
        else:
            credentials = self.__create_server_credentials(
                address, ca_for_discovery, cert_chain, enable_discovery, private_key, self.server_uuid
            )
            self.grpc_server.add_secure_port(address_string, server_credentials=credentials)

    def __start_zeroconf_broadcasting(self, address: str, port: int, ca_for_discovery: Optional[bytes]) -> None:
        logger.info("Starting zeroconf broadcasting for SiLA Server Discovery")
        if ca_for_discovery is None and self.generated_ca is not None:
            ca_for_discovery = self.generated_ca
        self.__service_broadcaster.register_server(self, address, port, ca=ca_for_discovery)

    def __create_server_credentials(
        self,
        address: str,
        ca_for_discovery: Optional[bytes],
        cert_chain: Optional[bytes],
        enable_discovery: bool,
        private_key: Optional[bytes],
        server_uuid: UUID,
    ) -> grpc.ServerCredentials:
        if private_key is None and cert_chain is None:
            if ca_for_discovery is not None:
                raise ValueError("A CA for use in discovery is only useful if certificate information is provided")
            if not enable_discovery:
                raise ValueError("If discovery is disabled, private key and certificate chain are required")

            logger.info("Generating self-signed certificate")
            private_key, cert_chain = generate_self_signed_certificate(server_uuid, address)

            self.generated_ca = cert_chain
        if private_key is None or cert_chain is None:
            raise ValueError(
                "For secure connections, either provide both the private key and certificate chain, "
                "or none of them (server will then generate a self-signed certificate)"
            )
        logger.info("Starting SiLA server with encryption")
        return grpc.ssl_server_credentials([(private_key, cert_chain)])

    def stop(self, grace_period: Optional[float] = None) -> None:
        """
        Stop the server and block until completion

        Parameters
        ----------
        grace_period: Time in seconds to wait before aborting all ongoing interactions
        """
        logger.info("Stopping server...")
        if self.__state != ServerState.RUNNING:
            raise RuntimeError("Can only stop running servers")

        # stop zeroconf broadcasting
        if self in self.__service_broadcaster.registered_server_infos:
            logger.debug("Stopping zeroconf broadcasting")
            self.__service_broadcaster.unregister_server(self)

        # stop feature implementations
        logger.debug("Stopping feature implementation servicers")
        for servicer in self.feature_servicers.values():
            servicer.cancel_all_subscriptions()
            servicer.implementation.stop()
        self.child_task_executor.shutdown(wait=True)

        # stop grpc server
        logger.debug("Stopping gRPC server if running")
        self.grpc_server.stop(grace_period).wait()
        logger.info("Stopped server")

        self.__state = ServerState.STOPPED

    def __add_sila_service(self):
        # import locally to prevent circular import
        from sila2.features.silaservice import SiLAServiceFeature
        from sila2.server.silaservice_impl import SiLAServiceImpl

        self.set_feature_implementation(SiLAServiceFeature, SiLAServiceImpl(parent_server=self))

    @property
    def running(self) -> bool:
        """True if the server is running, False otherwise"""
        return self.__state == ServerState.RUNNING

    def __getitem__(self, item: str) -> Feature:
        return self.features[item]

    def __del__(self):
        try:
            if self.__state == ServerState.RUNNING:
                self.stop()
        except AttributeError:  # when __init__ fails, some attributes might not exist yet, then they cannot be stopped
            pass

    @property
    def server_name(self) -> str:
        """SiLA Server Name."""
        return self.attributes.server_name

    @property
    def server_type(self) -> str:
        """SiLA Server Type."""
        return self.attributes.server_type

    @property
    def server_description(self) -> str:
        """SiLA Server Description."""
        return self.attributes.server_description

    @property
    def server_version(self) -> str:
        """SiLA Server Version."""
        return self.attributes.server_version

    @property
    def server_vendor_url(self) -> str:
        """SiLA Server URL."""
        return self.attributes.server_vendor_url

    @property
    def server_uuid(self) -> UUID:
        """SiLA Server UUID."""
        return self.attributes.server_uuid
