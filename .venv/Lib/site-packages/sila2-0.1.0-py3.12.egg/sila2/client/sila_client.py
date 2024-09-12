from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Type

import grpc

from sila2.client.client_feature import ClientFeature
from sila2.framework import DefinedExecutionError
from sila2.framework.defined_execution_error_node import DefinedExecutionErrorNode
from sila2.framework.fully_qualified_identifier import FullyQualifiedIdentifier

if TYPE_CHECKING:
    from sila2.features.silaservice import SiLAServiceClient
    from sila2.framework.utils import HasFullyQualifiedIdentifier


class SilaClient:
    SiLAService: SiLAServiceClient

    _channel: grpc.Channel
    _features: Dict[str, ClientFeature]
    _children_by_fully_qualified_identifier: Dict[FullyQualifiedIdentifier, HasFullyQualifiedIdentifier]
    _registered_defined_execution_error_classes: Dict[FullyQualifiedIdentifier, Type[DefinedExecutionError]]

    def __init__(self, hostname: str, port: int):
        self._channel = grpc.insecure_channel(f"{hostname}:{port}")
        self._features = {}
        self._children_by_fully_qualified_identifier = {}
        self._registered_defined_execution_error_classes = {}

        # import locally to prevent circular import
        from sila2.features.silaservice import SiLAServiceFeature, UnimplementedFeature

        self.__add_feature(SiLAServiceFeature._feature_definition)
        self._register_defined_execution_error_class(
            SiLAServiceFeature.defined_execution_errors["UnimplementedFeature"], UnimplementedFeature
        )

        for feature_id in self.SiLAService.ImplementedFeatures.get():
            if feature_id == self._features["SiLAService"].fully_qualified_identifier:
                continue
            self.__add_feature(self.SiLAService.GetFeatureDefinition(feature_id).FeatureDefinition)

    def __add_feature(self, feature_definition: str) -> None:
        feature = ClientFeature(feature_definition, self)
        self._children_by_fully_qualified_identifier[feature.fully_qualified_identifier] = feature
        self._children_by_fully_qualified_identifier.update(feature._children_by_fully_qualified_identifier)
        self._features[feature._identifier] = feature

        setattr(self, feature._identifier, feature)

    def _register_defined_execution_error_class(
        self, error_node: DefinedExecutionErrorNode, error_class: Type[DefinedExecutionError]
    ):
        self._registered_defined_execution_error_classes[error_node.fully_qualified_identifier] = error_class
