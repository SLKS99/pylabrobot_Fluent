from __future__ import annotations

import json
import os
from enum import Enum
from os.path import join
from typing import TYPE_CHECKING, Any, Union
from urllib.request import urlopen

import jsonschema
import xmlschema
from lxml import etree
from lxml.etree import XMLParser
from xmlschema import XMLSchemaValidationError

from sila2 import resource_dir
from sila2.framework.abc.constraint import Constraint
from sila2.framework.utils import xpath_sila

if TYPE_CHECKING:
    from sila2.framework.abc.data_type import DataType
    from sila2.framework.feature import Feature


class Schema(Constraint):
    schema_type: SchemaType
    source_type: SchemaSourceType
    source: str
    schema: Union[Any, xmlschema.XMLSchema, etree.XMLSchema]

    def __init__(self, schema_type: SchemaType, source_type: SchemaSourceType, source: str):
        self.schema_type = schema_type
        self.source_type = source_type
        self.source = source
        self.schema = self.get_schema()

    def validate(self, content: Union[str, bytes]) -> bool:
        if isinstance(self.schema, etree.XMLSchema):
            if isinstance(content, str):
                content = content.encode("utf-8")
            try:
                etree.fromstring(content, parser=XMLParser(schema=self.schema))
                return True
            except etree.XMLSyntaxError:
                return False
        elif isinstance(self.schema, xmlschema.XMLSchema):
            try:
                if isinstance(content, bytes):
                    content = content.decode("utf-8")
                self.schema.validate(content)
                return True
            except XMLSchemaValidationError:
                return False
        else:
            try:
                if isinstance(content, bytes):
                    content = content.decode("utf-8")
                jsonschema.validate(json.loads(content), schema=self.schema)
                return True
            except jsonschema.ValidationError:
                return False

    @classmethod
    def from_fdl_node(cls, fdl_node, parent_feature: Feature, base_type: DataType) -> Schema:
        _type = getattr(SchemaType, xpath_sila(fdl_node, "sila:Type/text()")[0])
        schema_node = xpath_sila(fdl_node, "sila:Inline|sila:Url")[0]
        source_type = getattr(SchemaSourceType, schema_node.xpath("name()"))
        schema_value = schema_node.text
        return cls(_type, source_type, schema_value)

    def get_schema(self) -> Union[Any, xmlschema.XMLSchema]:
        # XML
        if self.schema_type == SchemaType.Xml:
            if self.source_type == SchemaSourceType.Url:
                if "gitlab.com/sila2/sila_base" in self.source.lower() and self.source.split("/")[-1] in os.listdir(
                    join(resource_dir, "xsd")
                ):
                    return etree.XMLSchema(etree.parse(join(resource_dir, "xsd", self.source.split("/")[-1])))
                return xmlschema.XMLSchema(self.source)
            else:
                return etree.XMLSchema(etree.fromstring(self.source.encode("utf-8")))

        # JSON
        if self.source_type == SchemaSourceType.Inline:
            schema_str = self.source
        else:
            schema_str = urlopen(self.source).read().decode("utf-8")

        schema = json.loads(schema_str)
        validator_class = jsonschema.validators.validator_for(schema)
        validator_class.check_schema(schema)
        return schema

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.schema_type.name}, {self.source_type.name}, {self.source!r})"


class SchemaType(Enum):
    Xml = 0
    Json = 1


class SchemaSourceType(Enum):
    Inline = 0
    Url = 1
