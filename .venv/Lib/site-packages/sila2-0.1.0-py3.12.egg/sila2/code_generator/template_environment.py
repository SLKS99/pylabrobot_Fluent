from typing import Optional

from jinja2 import Environment

from sila2.code_generator.template_loader import TemplateLoader


class TemplateEnvironment(Environment):
    def __init__(self, template_subdir: Optional[str] = None):
        super().__init__(loader=TemplateLoader(template_subdir), autoescape=False)
        self.filters["repr"] = repr
        self.filters["strip"] = str.strip
        self.filters["lower"] = str.lower
