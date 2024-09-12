from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional, Type

from google.protobuf.message import Message

if TYPE_CHECKING:
    from sila2.framework.abc.named_data_node import NamedDataNode


class MessageMappable(ABC):
    """Abstract class all classes representing Python-mappings for protobuf messages"""

    message_type: Type[Message]
    native_type: Type

    @abstractmethod
    def to_native_type(self, message: Message, toplevel_named_data_node: Optional[NamedDataNode] = None) -> Any:
        """Convert a protobuf message to the associated native type"""
        pass

    @abstractmethod
    def to_message(self, *args, **kwargs) -> Message:
        """
        Construct a protobuf message from native objects

        Special kwargs:
        - toplevel_named_data_node: Optional[NamedDataNode]: The NamedDataNode object that the generated message is
            a part of (e.g. a Parameter instance)
        """
        pass
