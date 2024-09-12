from __future__ import annotations

import itertools as it
import os.path
from typing import List

from jinja2 import Environment

from sila2.code_generator.template_environment import TemplateEnvironment
from sila2.code_generator.template_objects.base import (
    ServerMetadata,
    ServerObservableCommand,
    ServerObservableProperty,
    ServerUnobservableCommand,
    ServerUnobservableProperty,
)
from sila2.code_generator.template_objects.basics import Field, Type
from sila2.code_generator.template_objects.client import (
    ClientMetadata,
    ClientObservableCommand,
    ClientObservableProperty,
    ClientUnobservableCommand,
    ClientUnobservableProperty,
)
from sila2.code_generator.template_objects.types import CompositeType, CompositeTypeField, TypeDefinition
from sila2.framework.data_types.data_type_definition import DataTypeDefinition
from sila2.framework.feature import Feature
from sila2.framework.utils import prettify_xml_string


class FeatureGenerator:
    feature: Feature
    template_env: Environment

    def __init__(self, feature: Feature) -> None:
        self.feature = feature
        self.template_env = TemplateEnvironment("feature")

    def generate_all(self, out_directory: str) -> None:
        prefix = self.feature._identifier.lower()

        os.makedirs(out_directory, exist_ok=True)
        open(os.path.join(out_directory, "__init__.py"), "w").write("")
        self.generate_feature(os.path.join(out_directory, f"{prefix}_feature.py"))
        with open(os.path.join(out_directory, f"{self.feature._identifier}.sila.xml"), "w") as fp:
            fp.write(prettify_xml_string(self.feature._feature_definition))

        self.generate_errors(os.path.join(out_directory, f"{prefix}_errors.py"))
        self.generate_types(os.path.join(out_directory, f"{prefix}_types.py"))
        self.generate_base(os.path.join(out_directory, f"{prefix}_base.py"))
        self.generate_client(os.path.join(out_directory, f"{prefix}_client.pyi"))
        self.generate_init(os.path.join(out_directory, "__init__.py"))

    def generate_errors(self, out_filename: str) -> None:
        content = self.template_env.get_template("errors").render(
            feature=self.feature, errors=self.feature.defined_execution_errors.values()
        )
        FeatureGenerator._generate_file(out_filename, content)

    def generate_init(self, out_filename: str) -> None:
        content = self.template_env.get_template("init").render(
            feature=self.feature,
        )
        FeatureGenerator._generate_file(out_filename, content)

    def generate_feature(self, out_filename: str) -> None:
        content = self.template_env.get_template("feature").render(feature=self.feature)
        FeatureGenerator._generate_file(out_filename, content)

    def generate_types(self, out_filename: str) -> None:
        message_types: List[CompositeType] = []
        for cmd in it.chain(
            self.feature._unobservable_commands.values(),
            self.feature._observable_commands.values(),
        ):
            message_types.append(
                CompositeType(
                    f"{cmd._identifier}_Responses", [CompositeTypeField.from_field(f) for f in cmd.responses.fields]
                )
            )
        for cmd in self.feature._observable_commands.values():
            if cmd.intermediate_responses:
                message_types.append(
                    CompositeType(
                        f"{cmd._identifier}_IntermediateResponses",
                        [CompositeTypeField.from_field(f) for f in cmd.intermediate_responses.fields],
                    )
                )

        definitions = [
            TypeDefinition(t._identifier, Type.from_data_type(t.data_type))
            for t in self.feature._data_type_definitions.values()
        ]

        content = self.template_env.get_template("types").render(
            named_tuples=message_types,
            data_type_definitions=definitions,
        )
        FeatureGenerator._generate_file(out_filename, content)

    def generate_base(self, out_filename: str) -> None:
        metadata = [ServerMetadata(m._identifier, m._description) for m in self.feature.metadata_definitions.values()]
        unobservable_properties = [
            ServerUnobservableProperty(p._identifier, Type.from_data_type(p.data_type), p._description)
            for p in self.feature._unobservable_properties.values()
        ]
        observable_properties = [
            ServerObservableProperty(p._identifier, Type.from_data_type(p.data_type), p._description)
            for p in self.feature._observable_properties.values()
        ]
        unobservable_commands = [
            ServerUnobservableCommand(
                cmd._identifier,
                [Field(p._identifier, Type.from_data_type(p.data_type), p._description) for p in cmd.parameters],
                [Field(r._identifier, Type.from_data_type(r.data_type), r._description) for r in cmd.responses],
                cmd._description,
            )
            for cmd in self.feature._unobservable_commands.values()
        ]
        observable_commands = [
            ServerObservableCommand(
                cmd._identifier,
                [Field(p._identifier, Type.from_data_type(p.data_type), p._description) for p in cmd.parameters],
                [
                    Field(i._identifier, Type.from_data_type(i.data_type), i._description)
                    for i in cmd.intermediate_responses
                ]
                if cmd.intermediate_responses is not None
                else [],
                [Field(r._identifier, Type.from_data_type(r.data_type), r._description) for r in cmd.responses],
                cmd._description,
            )
            for cmd in self.feature._observable_commands.values()
        ]

        imports = []
        for obj in it.chain(unobservable_properties, observable_properties, unobservable_commands, observable_commands):
            imports.extend(obj.imports)

        definition_imports = []
        for cmd in it.chain(self.feature._unobservable_commands.values(), self.feature._observable_commands.values()):
            for param in cmd.parameters:
                if isinstance(param.data_type, DataTypeDefinition):
                    definition_imports.append(param.data_type._identifier)

        content = self.template_env.get_template("base").render(
            feature=self.feature,
            imports=imports,
            metadata=metadata,
            unobservable_properties=unobservable_properties,
            observable_properties=observable_properties,
            unobservable_commands=unobservable_commands,
            observable_commands=observable_commands,
            definition_imports=definition_imports,
        )
        FeatureGenerator._generate_file(out_filename, content)

    def generate_client(self, out_filename: str) -> None:
        metadata = [ClientMetadata(m._identifier, m._description) for m in self.feature.metadata_definitions.values()]

        unobservable_properties = [
            ClientUnobservableProperty(prop._identifier, Type.from_data_type(prop.data_type), prop._description)
            for prop in self.feature._unobservable_properties.values()
        ]
        observable_properties = [
            ClientObservableProperty(prop._identifier, Type.from_data_type(prop.data_type), prop._description)
            for prop in self.feature._observable_properties.values()
        ]
        unobservable_commands = [
            ClientUnobservableCommand(
                cmd._identifier,
                [
                    Field(par._identifier, Type.from_data_type(par.data_type), par._description)
                    for par in cmd.parameters
                ],
                cmd._description,
            )
            for cmd in self.feature._unobservable_commands.values()
        ]
        observable_commands = [
            ClientObservableCommand(
                cmd._identifier,
                [
                    Field(par._identifier, Type.from_data_type(par.data_type), par._description)
                    for par in cmd.parameters
                ],
                cmd._description,
                bool(cmd.intermediate_responses),
            )
            for cmd in self.feature._observable_commands.values()
        ]

        imports = []
        for obj in it.chain(unobservable_properties, observable_properties, unobservable_commands, observable_commands):
            imports.extend(obj.imports)

        definition_imports = []
        for cmd in it.chain(self.feature._unobservable_commands.values(), self.feature._observable_commands.values()):
            for param in cmd.parameters:
                if isinstance(param.data_type, DataTypeDefinition):
                    definition_imports.append(param.data_type._identifier)

        content = self.template_env.get_template("client").render(
            feature=self.feature,
            imports=imports,
            metadata=metadata,
            unobservable_properties=unobservable_properties,
            observable_properties=observable_properties,
            unobservable_commands=unobservable_commands,
            observable_commands=observable_commands,
            definition_imports=definition_imports,
        )
        FeatureGenerator._generate_file(out_filename, content)

    @staticmethod
    def _generate_file(out_filename: str, content: str) -> None:
        with open(out_filename, "w") as fp:
            fp.write(content)
