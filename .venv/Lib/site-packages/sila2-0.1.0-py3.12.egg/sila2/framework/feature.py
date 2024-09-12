from __future__ import annotations

from types import ModuleType
from typing import TYPE_CHECKING, Dict, Optional, Type, Union

from sila2.framework.abc.named_node import NamedNode
from sila2.framework.command.command import Command
from sila2.framework.command.observable_command import ObservableCommand
from sila2.framework.command.unobservable_command import UnobservableCommand
from sila2.framework.data_types.data_type_definition import DataTypeDefinition
from sila2.framework.defined_execution_error_node import DefinedExecutionErrorNode
from sila2.framework.fully_qualified_identifier import FullyQualifiedIdentifier
from sila2.framework.metadata import Metadata
from sila2.framework.property.observable_property import ObservableProperty
from sila2.framework.property.property import Property
from sila2.framework.property.unobservable_property import UnobservableProperty
from sila2.framework.utils import (
    feature_definition_to_modules,
    parse_feature_definition,
    xml_node_to_normalized_string,
    xpath_sila,
)

if TYPE_CHECKING:
    from sila2.framework.abc.binary_transfer_handler import BinaryTransferHandler
    from sila2.framework.utils import HasFullyQualifiedIdentifier


class Feature(NamedNode):
    _feature_definition: str
    fully_qualified_identifier: FullyQualifiedIdentifier
    _sila2_version: str
    _feature_version: str
    _maturity_level: str
    _locale: str
    _originator: str
    _category: str
    _pb2_module: ModuleType
    _grpc_module: ModuleType
    _servicer_cls: Type
    _observable_properties: Dict[str, ObservableProperty]
    _unobservable_properties: Dict[str, UnobservableProperty]
    _observable_commands: Dict[str, ObservableCommand]
    _unobservable_commands: Dict[str, UnobservableCommand]
    _data_type_definitions: Dict[str, DataTypeDefinition]
    defined_execution_errors: Dict[str, DefinedExecutionErrorNode]
    metadata_definitions: Dict[str, Metadata]
    _binary_transfer_handler: Optional[BinaryTransferHandler]
    _children_by_fully_qualified_identifier: Dict[FullyQualifiedIdentifier, HasFullyQualifiedIdentifier]

    def __init__(self, feature_definition: str) -> None:
        fdl_node = parse_feature_definition(feature_definition)
        super().__init__(fdl_node)

        self._feature_definition = xml_node_to_normalized_string(fdl_node)

        self._sila2_version = fdl_node.attrib["SiLA2Version"]
        self._feature_version = fdl_node.attrib["FeatureVersion"]
        self._originator = fdl_node.attrib["Originator"]
        self._maturity_level = fdl_node.attrib.get("MaturityLevel", default="Draft")
        self._locale = fdl_node.attrib.get("Locale", default="en-us")
        self._category = fdl_node.attrib.get("Category", default="none")
        self.fully_qualified_identifier = FullyQualifiedIdentifier(
            f"{self._originator}/{self._category}/{self._identifier}/" f"v{self._feature_version.split('.')[0]}"
        )

        self._pb2_module, self._grpc_module = feature_definition_to_modules(fdl_node)
        self._servicer_cls = getattr(self._grpc_module, f"{self._identifier}Servicer")

        self._children_by_fully_qualified_identifier = {}

        self.defined_execution_errors = {}
        for err_node in xpath_sila(fdl_node, "sila:DefinedExecutionError"):
            err = DefinedExecutionErrorNode(err_node, self)
            self.defined_execution_errors[err._identifier] = err
            self._children_by_fully_qualified_identifier[err.fully_qualified_identifier] = err

        self._data_type_definitions = {}
        data_type_definition_nodes = list(xpath_sila(fdl_node, "sila:DataTypeDefinition"))
        failed_nodes = []
        while data_type_definition_nodes:
            num_nodes = len(data_type_definition_nodes)

            for dtype_node in data_type_definition_nodes:
                try:
                    dtype = DataTypeDefinition(dtype_node, self)
                    self._data_type_definitions[dtype._identifier] = dtype
                    self._children_by_fully_qualified_identifier[dtype.fully_qualified_identifier] = dtype
                except KeyError:
                    failed_nodes.append(dtype_node)

            if num_nodes == len(failed_nodes):
                identifiers = [NamedNode(node)._identifier for node in failed_nodes]
                raise ValueError(
                    f"Feature definition contains cyclic dependencies between data type definitions {identifiers}"
                )

            data_type_definition_nodes = failed_nodes
            failed_nodes = []

        self._observable_properties = {}
        self._unobservable_properties = {}
        for prop_node in xpath_sila(fdl_node, "sila:Property"):
            prop = Property.from_fdl_node(prop_node, self)
            self._children_by_fully_qualified_identifier[prop.fully_qualified_identifier] = prop
            if isinstance(prop, ObservableProperty):
                self._observable_properties[prop._identifier] = prop
            elif isinstance(prop, UnobservableProperty):
                self._unobservable_properties[prop._identifier] = prop
            else:
                raise NotImplementedError  # should never occur

        self._observable_commands = {}
        self._unobservable_commands = {}
        for command_node in xpath_sila(fdl_node, "sila:Command"):
            cmd = Command.from_fdl_node(command_node, self)
            self._children_by_fully_qualified_identifier[cmd.fully_qualified_identifier] = cmd
            for param in cmd.parameters:
                self._children_by_fully_qualified_identifier[param.fully_qualified_identifier] = param
            for resp in cmd.responses:
                self._children_by_fully_qualified_identifier[resp.fully_qualified_identifier] = resp
            if isinstance(cmd, ObservableCommand):
                self._observable_commands[cmd._identifier] = cmd
                if cmd.intermediate_responses is not None:
                    for int_resp in cmd.intermediate_responses:
                        self._children_by_fully_qualified_identifier[int_resp.fully_qualified_identifier] = int_resp
            elif isinstance(cmd, UnobservableCommand):
                self._unobservable_commands[cmd._identifier] = cmd
            else:
                raise NotImplementedError  # should never occur

        self.metadata_definitions = {}
        for meta_node in xpath_sila(fdl_node, "sila:Metadata"):
            meta = Metadata(meta_node, self)
            self.metadata_definitions[meta._identifier] = meta
            self._children_by_fully_qualified_identifier[meta.fully_qualified_identifier] = meta

        self._binary_transfer_handler = None

    def __getitem__(self, item: str) -> Union[Property, Command, Metadata]:
        if item in self._unobservable_properties:
            return self._unobservable_properties[item]
        if item in self._observable_properties:
            return self._observable_properties[item]
        if item in self._unobservable_commands:
            return self._unobservable_commands[item]
        if item in self._observable_commands:
            return self._observable_commands[item]
        if item in self.metadata_definitions:
            return self.metadata_definitions[item]
        raise KeyError(f"Feature '{self._identifier}' has no child command, property or metadata '{item}'")
