from __future__ import annotations

import os.path
import re
import sys
import tempfile
import warnings
from base64 import standard_b64encode
from collections import deque
from contextlib import contextmanager
from importlib import import_module
from os.path import abspath, join
from subprocess import PIPE, Popen
from types import ModuleType
from typing import TYPE_CHECKING, Generator, NoReturn, Tuple, Union

import grpc
from lxml import etree
from lxml.etree import XSLT, XMLParser, XMLSchema, _Element

from sila2 import resource_dir

if TYPE_CHECKING:
    from sila2.framework.abc.sila_error import SilaError
    from sila2.framework.binary_transfer.binary_transfer_error import BinaryTransferError
    from sila2.framework.command.command import Command
    from sila2.framework.command.intermediate_response import IntermediateResponse
    from sila2.framework.command.parameter import Parameter
    from sila2.framework.command.response import Response
    from sila2.framework.data_types.data_type_definition import DataTypeDefinition
    from sila2.framework.defined_execution_error_node import DefinedExecutionErrorNode
    from sila2.framework.feature import Feature
    from sila2.framework.metadata import Metadata
    from sila2.framework.property.property import Property
    from sila2.server.feature_implementation_servicer import FeatureImplementationServicer

    HasFullyQualifiedIdentifier = Union[
        Feature,
        Command,
        Property,
        Parameter,
        Response,
        IntermediateResponse,
        DefinedExecutionErrorNode,
        DataTypeDefinition,
        Metadata,
        FeatureImplementationServicer,
    ]


class FullyQualifiedIdentifierRegex:
    __originator_pattern = __category_pattern = r"[a-z][a-z\.]*"
    __identifier_pattern = r"[A-Z][a-zA-Z0-9]*"
    __major_version_pattern = r"v\d+"
    __feature_identifier_pattern = "/".join(
        (__originator_pattern, __category_pattern, __identifier_pattern, __major_version_pattern)
    )
    __command_identifier_pattern = "/".join((__feature_identifier_pattern, "Command", __identifier_pattern))

    FeatureIdentifier = __feature_identifier_pattern
    CommandIdentifier = __command_identifier_pattern
    CommandParameterIdentifier = "/".join((__command_identifier_pattern, "Parameter", __identifier_pattern))
    CommandResponseIdentifier = "/".join((__command_identifier_pattern, "Response", __identifier_pattern))
    IntermediateCommandResponseIdentifier = "/".join(
        (__command_identifier_pattern, "IntermediateResponse", __identifier_pattern)
    )
    DefinedExecutionErrorIdentifier = "/".join(
        (__feature_identifier_pattern, "DefinedExecutionError", __identifier_pattern)
    )
    PropertyIdentifier = "/".join((__feature_identifier_pattern, "Property", __identifier_pattern))
    TypeIdentifier = "/".join((__feature_identifier_pattern, "DataType", __identifier_pattern))
    MetadataIdentifier = "/".join((__feature_identifier_pattern, "Metadata", __identifier_pattern))


def parse_feature_definition(feature_definition: str):
    schema = XMLSchema(etree.parse(join(resource_dir, "xsd", "FeatureDefinition.xsd")))
    parser = XMLParser(schema=schema)
    return etree.fromstring(feature_definition.encode("utf-8"), parser=parser)


def xpath_sila(node, expression: str):
    """xpath with the `sila` namespace"""
    return node.xpath(expression, namespaces=dict(sila="http://www.sila-standard.org"))


def run_protoc(proto_file: str) -> Tuple[ModuleType, ModuleType]:
    path, filename = os.path.split(abspath(proto_file))
    modulename, _ = os.path.splitext(filename)

    include_framework = not proto_file.endswith("SiLAFramework.proto")

    with tempfile.TemporaryDirectory() as tmp_dir:
        protoc_command = [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
            f"--proto_path={path}",
            f"--proto_path={abspath(join(resource_dir, 'proto'))}",
            f"--python_out={tmp_dir}",
            f"--grpc_python_out={tmp_dir}",
            proto_file,
        ]
        if include_framework:
            protoc_command.append(abspath(join(resource_dir, "proto", "SiLAFramework.proto")))
        protoc_process = Popen(protoc_command, encoding="UTF-8", stderr=PIPE)
        _, protoc_stderr = protoc_process.communicate()

        error_lines, warning_lines = [], []
        for line in protoc_stderr.splitlines():
            if "warn" in line.lower():
                warning_lines.append(line)
            else:
                error_lines.append(line)

        for warning in warning_lines:
            warnings.warn(f"Warning during proto compilation: {warning}")

        if protoc_process.returncode != 0:
            raise RuntimeError(f"Failed to compile proto file {proto_file}: {os.linesep.join(error_lines)}")

        with temporarily_add_to_path(tmp_dir):
            pb2_module = import_module(f"{modulename}_pb2")
            grpc_module = import_module(f"{modulename}_pb2_grpc")

        del sys.modules[pb2_module.__name__]
        del sys.modules[grpc_module.__name__]

        return pb2_module, grpc_module


def feature_definition_to_modules(fdl_node) -> Tuple[ModuleType, ModuleType]:
    xslt = XSLT(etree.parse(join(resource_dir, "xsl", "fdl2proto.xsl")))
    proto_str = str(xslt(fdl_node))

    feature_id = xpath_sila(fdl_node, "sila:Identifier")[0].text
    with tempfile.TemporaryDirectory() as tmp_dir:
        proto_file = join(tmp_dir, f"{feature_id}.proto")
        with open(proto_file, "w", encoding="utf-8") as proto_fp:
            proto_fp.write(proto_str)

        return run_protoc(proto_file)


@contextmanager
def temporarily_add_to_path(*paths: str):
    sys.path.extend(paths)
    try:
        yield
    finally:
        for path in paths:
            sys.path.remove(path)


def xml_node_to_normalized_string(xml_node: _Element, remove_namespace: bool = False) -> str:
    if remove_namespace:
        str_with_namespace = etree.tostring(xml_node).decode("utf-8")
        str_without_namespace = re.sub(r"^<(\w+).*?>", r"<\1>", str_with_namespace)
        node_without_namespace = etree.fromstring(str_without_namespace)
        return etree.tostring(node_without_namespace, method="c14n2", strip_text=True).decode("utf-8")
    return etree.tostring(xml_node, method="c14n2", strip_text=True).decode("utf-8")


def prettify_xml_string(xml_string: str) -> str:
    node = etree.fromstring(xml_string, parser=etree.XMLParser(remove_blank_text=True))
    return str(etree.tostring(node, pretty_print=True), "utf-8")


def raise_as_rpc_error(error: Union[SilaError, BinaryTransferError], context: grpc.ServicerContext) -> NoReturn:
    context.abort(
        grpc.StatusCode.ABORTED, details=standard_b64encode(error.to_message().SerializeToString()).decode("ascii")
    )


def consume_generator(generator: Generator):
    """
    Exhausts a generator and discards its content

    From Itertools Recipes: https://docs.python.org/3/library/itertools.html#itertools-recipes
    """
    deque(generator, maxlen=0)
