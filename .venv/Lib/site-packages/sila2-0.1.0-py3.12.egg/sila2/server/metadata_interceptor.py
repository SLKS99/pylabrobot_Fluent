from abc import ABC, abstractmethod
from typing import Any, Dict

from sila2.framework.fully_qualified_identifier import FullyQualifiedIdentifier


class MetadataInterceptor(ABC):
    @abstractmethod
    def intercept(
        self, parameters: Any, metadata: Dict[FullyQualifiedIdentifier, Any], target_call: FullyQualifiedIdentifier
    ) -> None:
        pass
