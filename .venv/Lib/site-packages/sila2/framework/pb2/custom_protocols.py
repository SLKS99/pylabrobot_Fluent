from typing import List, Protocol

from sila2.framework.pb2 import SiLAFramework_pb2
from sila2.framework.pb2.SiLAFramework_pb2 import String


class AffectedCallsMessage(Protocol):
    AffectedCalls: List[String]

    def __init__(self, AffectedCalls: List[String]):
        self.AffectedCalls = AffectedCalls


class FeatureProtobufModule(Protocol):
    SiLAFramework__pb2: SiLAFramework_pb2
