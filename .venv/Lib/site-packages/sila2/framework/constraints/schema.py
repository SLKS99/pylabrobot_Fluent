from __future__ import annotations

import json
import os
import warnings
from enum import Enum
from os.path import join
from typing import TYPE_CHECKING, Any, Optional, TypeVar, Union
from urllib.request import urlopen

from lxml import etree
from lxml.etree import XMLParser

from sila2 import resource_dir
from sila2.config import ENCODING
from sila2.framework.abc.constraint import Constraint
from sila2.framework.utils import xpath_sila

if TYPE_CHECKING:
    from sila2.framework.abc.data_type import DataType
    from sila2.framework.feature import Feature

JSONSCHEMA_INSTALLED = False
try:
    import jsonschema

    JSONSCHEMA_INSTALLED = True
except ImportError:
    pass

XMLSCHEMA_INSTALLED = False
try:
    import xmlschema
    from xmlschema import XMLSchemaValidationError

    XMLSCHEMA_INSTALLED = True
except ImportError:
    pass


T = TypeVar("T", bound=Union[str, bytes])


class Schema(Constraint[T]):
    schema_type: SchemaType
    source_type: SchemaSourceType
    source: str
    schema: Optional[Union[Any, xmlschema.XMLSchema, etree.XMLSchema]]
    schema_lib_installed: bool

    def __init__(self, schema_type: SchemaType, source_type: SchemaSourceType, source: str):
        if schema_type is SchemaType.Xml:
            self.schema_lib_installed = XMLSCHEMA_INSTALLED
        else:
            self.schema_lib_installed = JSONSCHEMA_INSTALLED

        self.schema_type = schema_type
        self.source_type = source_type
        self.source = source
        self.schema = self.get_schema()

    def validate(self, content: T) -> bool:
        if self.schema is None:
            return True

        if isinstance(self.schema, etree.XMLSchema):
            if isinstance(content, str):
                content = content.encode(ENCODING)
            try:
                etree.fromstring(  # noqa: S320 (don't resolve entities on untrusted XML input)
                    content, parser=XMLParser(schema=self.schema, resolve_entities=False)
                )
                return True
            except etree.XMLSyntaxError:
                return False
        elif isinstance(self.schema, xmlschema.XMLSchema):
            try:
                if isinstance(content, bytes):
                    content = content.decode(ENCODING)
                self.schema.validate(content)
                return True
            except XMLSchemaValidationError:
                return False
        else:
            try:
                if isinstance(content, bytes):
                    content = content.decode(ENCODING)
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

    def get_schema(self) -> Optional[Union[Any, xmlschema.XMLSchema]]:
        # XML
        if self.schema_type == SchemaType.Xml:
            if self.source_type == SchemaSourceType.Url:
                if "gitlab.com/sila2/sila_base" in self.source.lower() and self.source.split("/")[-1] in os.listdir(
                    join(resource_dir, "xsd")
                ):
                    with open(join(resource_dir, "xsd", self.source.split("/")[-1]), encoding=ENCODING) as fp:
                        return etree.XMLSchema(etree.parse(fp))  # noqa: S320 (trusted XML input)

                if not XMLSCHEMA_INSTALLED:
                    warnings.warn(
                        "Found XML Schema constraint, but `xmlschema` is not installed. Constraint will be ignored."
                    )
                    return None
                return xmlschema.XMLSchema(self.source, defuse="always")

            # inline schema
            return etree.XMLSchema(
                etree.fromstring(  # noqa: S320 (don't resolve entities on untrusted input)
                    self.source.encode(ENCODING), parser=etree.XMLParser(resolve_entities=False)
                )
            )

        # JSON
        if not JSONSCHEMA_INSTALLED:
            warnings.warn(
                "Found JSON Schema constraint, but `jsonschema` is not installed. Constraint will be ignored."
            )
            return None

        if self.source_type == SchemaSourceType.Inline:
            schema_str = self.source
        else:
            url = self.source
            if not url.startswith(("http:", "https:")):
                raise ValueError("URL must start with 'http:' or 'https:'")

            with urlopen(url) as response:  # noqa: S310, only allow http and https (ruff bug?)
                schema_str = response.read().decode(ENCODING)

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
