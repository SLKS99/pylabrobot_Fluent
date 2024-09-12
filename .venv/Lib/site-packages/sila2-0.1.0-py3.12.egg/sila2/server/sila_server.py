from __future__ import annotations

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Dict, List, Optional, Union
from uuid import UUID

import grpc

from sila2.discovery.broadcaster import SilaServiceBroadcaster
from sila2.discovery.service_info import SilaServiceInfo
from sila2.framework.binary_transfer.server_binary_transfer_handler import ServerBinaryTransferHandler
from sila2.framework.constraints.maximal_length import MaximalLength
from sila2.framework.constraints.pattern import Pattern
from sila2.framework.feature import Feature
from sila2.framework.fully_qualified_identifier import FullyQualifiedIdentifier
from sila2.framework.utils import parse_feature_definition, xpath_sila
from sila2.server.feature_implementation_base import FeatureImplementationBase
from sila2.server.feature_implementation_servicer import FeatureImplementationServicer
from sila2.server.metadata_interceptor import MetadataInterceptor

if TYPE_CHECKING:
    from sila2.framework.utils import HasFullyQualifiedIdentifier

logger = logging.getLogger(__name__)


class SilaServer:
    grpc_server: grpc.Server
    features: Dict[str, Feature]
    feature_servicers: Dict[str, FeatureImplementationServicer]

    server_name: str
    server_type: str
    server_uuid: UUID
    server_description: str
    server_version: str
    server_vendor_url: str

    service_broadcaster: SilaServiceBroadcaster
    running_instances: List[SilaServiceInfo]

    binary_transfer_handler: ServerBinaryTransferHandler

    metadata_interceptors: List[MetadataInterceptor]

    children_by_fully_qualified_identifier: Dict[FullyQualifiedIdentifier, HasFullyQualifiedIdentifier]

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
    ):
        # import locally to prevent circular import
        from sila2.features.silaservice import SiLAServiceFeature
        from sila2.server.silaservice_impl import SiLAServiceImpl

        silaservice_fdl_tree = parse_feature_definition(SiLAServiceFeature._feature_definition)

        name_constraint = MaximalLength(
            int(
                xpath_sila(
                    silaservice_fdl_tree,
                    "//sila:Command[sila:Identifier/text() = 'SetServerName']//sila:MaximalLength/text()",
                )[0]
            )
        )
        type_constraint = Pattern(
            xpath_sila(
                silaservice_fdl_tree, "//sila:Property[sila:Identifier/text() = 'ServerType']//sila:Pattern/text()"
            )[0]
        )
        version_constraint = Pattern(
            xpath_sila(
                silaservice_fdl_tree, "//sila:Property[sila:Identifier/text() = 'ServerVersion']//sila:Pattern/text()"
            )[0]
        )
        vendor_url_constraint = Pattern(
            xpath_sila(
                silaservice_fdl_tree, "//sila:Property[sila:Identifier/text() = 'ServerVendorURL']//sila:Pattern/text()"
            )[0]
        )

        if not name_constraint.validate(server_name):
            raise ValueError(f"Server name {server_name!r} does not satisfy constraint {name_constraint!r}")
        if not type_constraint.validate(server_type):
            raise ValueError(f"Server type {server_type!r} does not satisfy constraint {type_constraint!r}")
        if not version_constraint.validate(server_version):
            raise ValueError(
                f"Server version {server_version!r} does not satisfy constraint {version_constraint!r}. "
                f"Examples: '2.1', '0.1.3', '1.2.3_preview'"
            )
        if not vendor_url_constraint.validate(server_vendor_url):
            raise ValueError(
                f"Server vendor url {server_vendor_url!r} does not satisfy constraint {vendor_url_constraint!r}"
            )

        self.server_name = server_name
        self.server_type = server_type
        if server_uuid is None:
            self.server_uuid = uuid.uuid4()
        else:
            self.server_uuid = server_uuid if isinstance(server_uuid, UUID) else UUID(server_uuid)
        self.server_description = server_description
        self.server_version = server_version
        self.server_vendor_url = server_vendor_url

        self.grpc_server = grpc.server(
            ThreadPoolExecutor(max_workers=max_grpc_workers, thread_name_prefix=f"grpc-executor-{self.server_uuid}")
        )
        self.service_broadcaster = SilaServiceBroadcaster()
        self.running_instances = []
        self.features = {}
        self.feature_servicers = {}
        self.metadata_interceptors = []

        self.binary_transfer_handler = ServerBinaryTransferHandler(self.grpc_server)

        self.child_task_executor = ThreadPoolExecutor(
            max_workers=max_child_task_workers, thread_name_prefix=f"child-task-executor-{self.server_uuid}"
        )

        self.children_by_fully_qualified_identifier = {}

        self.set_feature_implementation(SiLAServiceFeature, SiLAServiceImpl(parent_server=self))

    def set_feature_implementation(self, feature: Feature, implementation: FeatureImplementationBase):
        if feature._identifier in self.feature_servicers:
            self.feature_servicers[feature._identifier].implementation.stop()

        class FeatureServicer(FeatureImplementationServicer, feature._servicer_cls):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._set_implementation(implementation)

        servicer: FeatureImplementationServicer = FeatureServicer(self, feature)
        self.features[feature._identifier] = feature
        self.feature_servicers[feature._identifier] = servicer

        # add self as servicer to the gRPC server
        getattr(feature._grpc_module, f"add_{feature._identifier}Servicer_to_server")(servicer, self.grpc_server)

        feature._binary_transfer_handler = self.binary_transfer_handler
        self.children_by_fully_qualified_identifier[feature.fully_qualified_identifier] = feature
        self.children_by_fully_qualified_identifier.update(feature._children_by_fully_qualified_identifier)

    def add_metadata_interceptor(self, interceptor: MetadataInterceptor):
        self.metadata_interceptors.append(interceptor)

    def start_insecure(self, address: str, port: int, enable_discovery: bool = True):
        logger.info(f"Starting server {self.server_name} ({self.server_uuid}) on insecure {address}:{port}")

        for servicer in self.feature_servicers.values():
            servicer.implementation.start()

        self.grpc_server.add_insecure_port(f"{address}:{port}")
        self.grpc_server.start()

        if enable_discovery:
            info = self.service_broadcaster.register_server(self, address, port)
            self.running_instances.append(info)

    def stop(self, grace_period: Optional[float] = None):
        stop_event = self.grpc_server.stop(grace_period)
        for info in self.running_instances:
            self.service_broadcaster.unregister_server(info)
            self.running_instances.remove(info)
        for servicer in self.feature_servicers.values():
            servicer.cancel_all_subscriptions()
            servicer.implementation.stop()
        self.child_task_executor.shutdown(wait=True)
        stop_event.wait()

    def __getitem__(self, item: str) -> Feature:
        return self.features[item]

    def __del__(self):
        self.stop()
