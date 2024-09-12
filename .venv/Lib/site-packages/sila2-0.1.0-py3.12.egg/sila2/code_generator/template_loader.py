import os
from typing import Optional

from jinja2 import FileSystemLoader

from sila2 import resource_dir


class TemplateLoader(FileSystemLoader):
    def __init__(self, template_subdir: Optional[str] = None):
        template_dir = os.path.join(resource_dir, "code_generator_templates")
        if template_subdir is not None:
            template_dir = os.path.join(template_dir, template_subdir)
        super().__init__(searchpath=template_dir, encoding="utf-8")

    def get_source(self, environment, template: str):
        return super().get_source(environment, f"{template}.jinja2")
