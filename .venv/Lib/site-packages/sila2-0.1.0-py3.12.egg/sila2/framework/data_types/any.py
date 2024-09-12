from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any as TypingAny
from typing import NamedTuple, Optional, Type

from sila2.framework.abc.data_type import DataType
from sila2.framework.abc.named_data_node import NamedDataNode
from sila2.framework.data_types.list import List

if TYPE_CHECKING:
    from sila2.pb2_stubs import SiLAFramework_pb2
    from sila2.pb2_stubs.SiLAFramework_pb2 import Any as SilaAny


class SilaAnyType(NamedTuple):
    type_xml: str
    value: TypingAny


class Any(DataType):
    native_type = SilaAnyType
    message_type: Type[SilaAny]

    def __init__(self, silaframework_pb2_module: SiLAFramework_pb2):
        self.message_type = silaframework_pb2_module.Any

    def to_native_type(self, message: SilaAny, toplevel_named_data_node: Optional[NamedDataNode] = None) -> SilaAnyType:
        _type_str = message.type
        data_type = Any.__getdata_type(_type_str)
        msg = data_type.message_type.FromString(message.payload)
        return SilaAnyType(_type_str, data_type.to_native_type(msg, toplevel_named_data_node=toplevel_named_data_node))

    def to_message(self, value: SilaAnyType, toplevel_named_data_node: Optional[NamedDataNode] = None) -> SilaAny:
        _type, native_payload = value
        data_type = Any.__getdata_type(_type)
        binary_payload = data_type.to_message(
            native_payload, toplevel_named_data_node=toplevel_named_data_node
        ).SerializeToString()

        return self.message_type(type=_type, payload=binary_payload)

    @staticmethod
    def __getdata_type(type_xml_str: str) -> DataType:
        from sila2.framework.feature import Feature

        fdl_str = Any.__build_feature_xml(type_xml_str)
        data_type = Feature(fdl_str)._data_type_definitions["Any"]

        if isinstance(data_type, List):
            raise NotImplementedError("Any with List is not yet implemented")

        return data_type

    @staticmethod
    def __build_feature_xml(type_xml_str: str) -> str:
        return f"""<?xml version="1.0" encoding="utf-8" ?>
        <Feature SiLA2Version="1.0" FeatureVersion="1.0" Originator="org.silastandard"
                 Category="tests"
                 xmlns="http://www.sila-standard.org"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xsi:schemaLocation="http://www.sila-standard.org https://gitlab.com/SiLA2/sila_base/raw/master/schema/FeatureDefinition.xsd">
            <Identifier>Any</Identifier>
            <DisplayName>Any</DisplayName>
            <Description>Dummy feature for the SiLA2 Any type</Description>
            <DataTypeDefinition>
                <Identifier>Any</Identifier>
                <DisplayName>Any</DisplayName>
                <Description>Any</Description>
                {type_xml_str}
            </DataTypeDefinition>
        </Feature>"""
