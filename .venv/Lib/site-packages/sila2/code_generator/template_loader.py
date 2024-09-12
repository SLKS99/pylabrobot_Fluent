import os

from jinja2 import FileSystemLoader

from sila2 import resource_dir
from sila2.config import ENCODING


class TemplateLoader(FileSystemLoader):
    def __init__(self):
        template_dir = os.path.join(resource_dir, "code_generator_templates")
        super().__init__(searchpath=template_dir, encoding=ENCODING)

    def get_source(self, environment, template: str):
        return super().get_source(environment, f"{template}.jinja2")
