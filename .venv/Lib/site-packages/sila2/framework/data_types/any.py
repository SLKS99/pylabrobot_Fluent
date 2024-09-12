from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Iterable, NamedTuple, Optional
from typing import Any as TypingAny

from lxml import etree

from sila2.framework.abc.data_type import DataType
from sila2.framework.abc.named_data_node import NamedDataNode
from sila2.framework.pb2 import SiLAFramework_pb2
from sila2.framework.pb2.SiLAFramework_pb2 import Any as SilaAny
from sila2.framework.utils import xml_node_to_normalized_string

if TYPE_CHECKING:
    from sila2.client import ClientMetadataInstance
    from sila2.framework import DataTypeDefinition

VOID_TYPE_XML = """
<DataType>
  <Constrained>
    <DataType>
      <Basic>String</Basic>
    </DataType>
    <Constraints>
      <Length>0</Length>
    </Constraints>
  </Constrained>
</DataType>
"""


class SilaAnyType(NamedTuple):
    type_xml: str
    """
    DataType element, must adhere to
    `AnyTypeDataType.xsd <https://gitlab.com/SiLA2/sila_base/-/blob/master/schema/AnyTypeDataType.xsd>`_
    """
    value: TypingAny
    """Value of the given type"""

    @staticmethod
    def create_void() -> SilaAnyType:
        """Create an instance representing Python's ``None`` (called "Void" in SiLA)."""
        return SilaAnyType(xml_node_to_normalized_string(VOID_TYPE_XML), None)


class Any(DataType[SilaAny, SilaAnyType]):
    message_type = SiLAFramework_pb2.Any

    def to_native_type(self, message: SilaAny, toplevel_named_data_node: Optional[NamedDataNode] = None) -> SilaAnyType:
        type_str = message.type
        data_type = Any.__getdata_type(type_str)

        msg = data_type.message_type.FromString(message.payload)
        native_value = data_type.to_native_type(msg, toplevel_named_data_node=toplevel_named_data_node)

        if native_value == "" and Any.__is_void(type_str):
            native_value = None

        return SilaAnyType(xml_node_to_normalized_string(type_str), native_value)

    def to_message(
        self,
        value: SilaAnyType,
        toplevel_named_data_node: Optional[NamedDataNode] = None,
        metadata: Optional[Iterable[ClientMetadataInstance]] = None,
    ) -> SilaAny:
        type_str, native_payload = value
        type_str = xml_node_to_normalized_string(type_str)

        if Any.__is_void(type_str) and native_payload is None:
            native_payload = ""

        data_type = Any.__getdata_type(type_str)
        message = data_type.to_message(
            native_payload, toplevel_named_data_node=toplevel_named_data_node, metadata=metadata
        )

        binary_payload = message.SerializeToString()
        return SiLAFramework_pb2.Any(type=type_str, payload=binary_payload)

    @staticmethod
    def __is_void(type_xml_str: str) -> bool:
        type_node = etree.fromstring(  # noqa: S320 (don't resolve entities on untrusted XML input)
            type_xml_str, parser=etree.XMLParser(resolve_entities=False)
        )
        return xml_node_to_normalized_string(type_node) == xml_node_to_normalized_string(VOID_TYPE_XML)

    @staticmethod
    def __getdata_type(type_xml_str: str) -> DataTypeDefinition:
        from sila2.framework.feature import Feature

        feature_xml = Any.__build_feature_xml(type_xml_str)

        return Feature(feature_xml)._data_type_definitions["Any"]

    @staticmethod
    def __build_feature_xml(type_xml_str: str) -> str:
        return f"""\
<?xml version="1.0" encoding="utf-8" ?>
<Feature SiLA2Version="1.0" FeatureVersion="1.0" Originator="org.silastandard"
         Category="tests"
         xmlns="http://www.sila-standard.org"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://www.sila-standard.org
             https://gitlab.com/SiLA2/sila_base/raw/master/schema/FeatureDefinition.xsd">
    <Identifier>AnyFeature{str(uuid.uuid4()).replace("-", "")}</Identifier>
    <DisplayName>Any</DisplayName>
    <Description>Dummy feature for the SiLA2 Any type</Description>
    <DataTypeDefinition>
        <Identifier>Any</Identifier>
        <DisplayName>Any</DisplayName>
        <Description>Any</Description>
        {type_xml_str}
    </DataTypeDefinition>
</Feature>"""
