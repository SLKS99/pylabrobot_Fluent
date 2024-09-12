from __future__ import annotations

import ipaddress
import os.path
import re
import socket
import sys
import tempfile
from base64 import standard_b64encode
from collections import deque
from contextlib import contextmanager
from importlib import import_module
from os.path import abspath, join
from types import ModuleType
from typing import TYPE_CHECKING, Generator, List, NoReturn, Tuple, Union

import grpc
from grpc_tools import protoc
from lxml import etree
from lxml.etree import XSLT, XMLParser, XMLSchema, XSLTApplyError, _Element

from sila2 import resource_dir
from sila2.config import ENCODING
from sila2.framework.pb2.custom_protocols import FeatureProtobufModule

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
    ]


class FullyQualifiedIdentifierRegex:
    originator = __category = r"[a-z][a-z\.]*"
    identifier = r"[A-Z][a-zA-Z0-9]*"
    major_version = r"v\d+"

    FeatureIdentifier = f"{originator}/{__category}/{identifier}/{major_version}"
    CommandIdentifier = f"{FeatureIdentifier}/Command/{identifier}"
    CommandParameterIdentifier = f"{CommandIdentifier}/Parameter/{identifier}"
    CommandResponseIdentifier = f"{CommandIdentifier}/Response/{identifier}"
    IntermediateCommandResponseIdentifier = f"{CommandIdentifier}/IntermediateResponse/{identifier}"
    DefinedExecutionErrorIdentifier = f"{FeatureIdentifier}/DefinedExecutionError/{identifier}"
    PropertyIdentifier = f"{FeatureIdentifier}/Property/{identifier}"
    DataTypeIdentifier = f"{FeatureIdentifier}/DataType/{identifier}"
    MetadataIdentifier = f"{FeatureIdentifier}/Metadata/{identifier}"


def parse_feature_definition(feature_definition: str) -> etree._Element:
    """
    Parse a feature definition (content of a .sila.xml file) and return the root node of the XML document

    Parameters
    ----------
    feature_definition
        Feature definition (XML) as string, or path to a feature definition file

    Returns
    -------
    fdl_root
        Root node of the XML document
    """
    with open(join(resource_dir, "xsd", "FeatureDefinition.xsd"), encoding=ENCODING) as fp:
        schema = XMLSchema(etree.parse(fp))  # noqa: S320 (parse trusted XML file)

    if os.path.isfile(feature_definition) or feature_definition.endswith(".sila.xml"):
        with open(feature_definition, "rb") as fdl_file:
            feature_definition_bytes = fdl_file.read()
            if feature_definition_bytes.startswith(b"<"):
                feature_definition = feature_definition_bytes.decode(ENCODING)
            elif feature_definition_bytes.startswith(b"\xef\xbb\xbf"):
                feature_definition = feature_definition_bytes[3:].decode(ENCODING)
            else:
                raise ValueError("Expected a UTF-8 encoded file")

    return etree.fromstring(  # noqa: S320 (untrusted input -> don't resolve entities)
        feature_definition.encode(ENCODING),
        parser=(XMLParser(schema=schema, encoding=ENCODING, resolve_entities=False)),
    )


def xpath_sila(node, expression: str):
    """xpath with the `sila` namespace"""
    return node.xpath(expression, namespaces={"sila": "http://www.sila-standard.org"})


def run_protoc(proto_file: str) -> Tuple[FeatureProtobufModule, ModuleType]:
    path, filename = os.path.split(abspath(proto_file))
    modulename, _ = os.path.splitext(filename)

    with tempfile.TemporaryDirectory() as tmp_dir:
        protoc_args = [
            "protoc",  # protoc expects args[0] to be the program name, which is irrelevant here and will be ignored
            f"--proto_path={path}",
            f"--proto_path={abspath(join(resource_dir, 'proto'))}",
            f"--python_out={tmp_dir}",
            f"--grpc_python_out={tmp_dir}",
            proto_file,
        ]
        if filename != "SiLAFramework.proto":
            protoc_args.append(abspath(join(resource_dir, "proto", "SiLAFramework.proto")))
        if protoc.main(protoc_args) != 0:
            raise RuntimeError(f"Failed to compile proto file {proto_file}")

        with temporarily_add_to_path(tmp_dir):
            pb2_module: FeatureProtobufModule = import_module(f"{modulename}_pb2")
            grpc_module = import_module(f"{modulename}_pb2_grpc")

        del sys.modules[pb2_module.__name__]
        del sys.modules[grpc_module.__name__]

        return pb2_module, grpc_module


def feature_definition_to_proto_string(fdl_node: _Element) -> str:
    with open(join(resource_dir, "xsl", "fdl2proto.xsl"), encoding=ENCODING) as fp:
        xslt = XSLT(etree.parse(fp))  # noqa: S320 (parse trusted XML file)

    try:
        return str(xslt(fdl_node))
    except XSLTApplyError as ex:
        raise ValueError(f"Invalid feature definition: {ex}")


def feature_definition_to_modules(fdl_node) -> Tuple[FeatureProtobufModule, ModuleType]:
    proto_str = feature_definition_to_proto_string(fdl_node)

    feature_id = xpath_sila(fdl_node, "sila:Identifier")[0].text
    with tempfile.TemporaryDirectory() as tmp_dir:
        proto_file = join(tmp_dir, f"{feature_id}.proto")
        with open(proto_file, "w", encoding=ENCODING) as proto_fp:
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


def xml_node_to_normalized_string(xml_node: Union[str, _Element], remove_namespace: bool = False) -> str:
    if isinstance(xml_node, str):
        xml_node = etree.fromstring(  # noqa: S320 (don't resolve entities on untrusted XML input)
            xml_node, parser=XMLParser(resolve_entities=False)
        )

    if remove_namespace:
        str_with_namespace = etree.tostring(xml_node).decode(ENCODING)
        str_without_namespace = re.sub(r"^<(\w+).*?>", r"<\1>", str_with_namespace)
        node_without_namespace = etree.fromstring(str_without_namespace)  # noqa: S320 (parse trusted XML string)
        return etree.tostring(node_without_namespace, method="c14n2", strip_text=True).decode(ENCODING)

    return etree.tostring(xml_node, method="c14n2", strip_text=True).decode(ENCODING)


def raise_as_rpc_error(error: Union[SilaError, BinaryTransferError], context: grpc.ServicerContext) -> NoReturn:
    context.abort(
        grpc.StatusCode.ABORTED, details=standard_b64encode(error.to_message().SerializeToString()).decode("ascii")
    )


def consume_generator(generator: Generator) -> None:
    """
    Exhausts a generator and discards its content

    From Itertools Recipes: https://docs.python.org/3/library/itertools.html#itertools-recipes
    """
    deque(generator, maxlen=0)


def resolve_host_to_ip_addresses(host: str) -> List[str]:
    """
    Convert a given host (name or address) to the associated ip address(es)

    If the host is ``0.0.0.0`` (all available addresses), this function returns the IP addresses of localhost and
    ``socket.gethostname()``.
    """
    if host == "0.0.0.0":  # noqa: S104, binding to all interfaces
        # host is all local IPv4 addresses
        return [
            socket.gethostbyname(socket.gethostname()),
            socket.gethostbyname("localhost"),
        ]

    try:
        # host is IP address
        return [ipaddress.ip_address(host).exploded]
    except ValueError:
        try:
            # host is a valid hostname
            return [socket.gethostbyname(host)]
        except socket.gaierror as e:
            raise ValueError(f"Failed to resolve host '{host}': {e.strerror}")


def running_in_docker() -> bool:
    if os.path.exists("/.dockerenv"):
        return True

    cgroup_file = "/proc/self/cgroup"
    if not os.path.isfile(cgroup_file):
        return False

    with open(cgroup_file, encoding=ENCODING) as cgroup_fp:
        for line in cgroup_fp:
            if ":/docker/" in line:
                return True
    return False
