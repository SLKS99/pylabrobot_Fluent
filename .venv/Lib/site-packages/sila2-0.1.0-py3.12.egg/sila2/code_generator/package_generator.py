import os
import sys
from os.path import join
from typing import Iterable, Optional

from sila2.code_generator.feature_generator import FeatureGenerator
from sila2.code_generator.template_environment import TemplateEnvironment
from sila2.framework import Feature


class PackageGenerator:
    def __init__(
        self,
        out_directory: str,
        package_name: Optional[str],
        features: Iterable[Feature],
        overwrite: bool,
    ):
        self.generate_package = package_name is not None

        if self.generate_package and not package_name.isidentifier():
            raise ValueError(f"Expected a valid package name, got {package_name!r}")

        self.out_directory = out_directory  # will be changed later
        self.package_name = package_name
        self.features = tuple(features)
        self.template_env = TemplateEnvironment("package")
        self.overwrite = overwrite

    def generate(self) -> None:
        if self.generate_package:
            # set out directory to package level
            os.makedirs(self.out_directory, exist_ok=True)
            original_out_directory = self.out_directory

            self._generate_file(
                join(self.out_directory, "setup.py"),
                self.template_env.get_template("setup").render(package_name=self.package_name),
            )
            self._generate_file(
                join(self.out_directory, "MANIFEST.in"),
                self.template_env.get_template("manifest").render(package_name=self.package_name),
            )

            # set out directory to package source code level
            self.out_directory = join(self.out_directory, self.package_name)
            os.makedirs(self.out_directory, exist_ok=True)

            self._generate_file(
                join(self.out_directory, "__main__.py"),
                self.template_env.get_template("main").render(package_name=self.package_name),
            )
            self._generate_file(
                join(self.out_directory, "__init__.py"),
                self.template_env.get_template("init").render(package_name=self.package_name),
            )
            self._generate_file(
                join(self.out_directory, "server.py"),
                self.template_env.get_template("server").render(package_name=self.package_name, features=self.features),
            )
            self.out_directory = join(self.out_directory, "generated")
        else:
            # set out directory to auto-generated source code level
            original_out_directory = self.out_directory

        os.makedirs(self.out_directory, exist_ok=True)
        self._generate_file(join(self.out_directory, "__init__.py"), "")
        self._generate_file(
            join(self.out_directory, "client.py"),
            self.template_env.get_template("client").render(package_name=self.package_name, features=self.features),
        )

        for feature in self.features:
            FeatureGenerator(feature).generate_all(join(self.out_directory, feature._identifier.lower()))

        os.system(f"{sys.executable} -m isort --line-length 120 --quiet --profile black {original_out_directory}")
        os.system(f"{sys.executable} -m black --line-length 120 --quiet {original_out_directory}")

    def _generate_file(self, out_filename: str, content: str) -> None:
        if not self.overwrite and os.path.isfile(out_filename):
            raise FileExistsError(f"File '{out_filename}' already exists. Set --overwrite to overwrite existing files.")
        with open(out_filename, "w") as fp:
            fp.write(content)
