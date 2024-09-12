from __future__ import annotations

from datetime import date, tzinfo
from typing import TYPE_CHECKING, NamedTuple, Optional, Type

from sila2.framework.abc.data_type import DataType
from sila2.framework.abc.named_data_node import NamedDataNode
from sila2.framework.data_types.timezone import Timezone

if TYPE_CHECKING:
    from sila2.pb2_stubs import SiLAFramework_pb2
    from sila2.pb2_stubs.SiLAFramework_pb2 import Date as SilaDate


class SilaDateType(NamedTuple):
    date: date
    timezone: tzinfo


class Date(DataType):
    native_type = SilaDateType
    message_type: Type[SilaDate]

    def __init__(self, silaframework_pb2_module: SiLAFramework_pb2):
        self.message_type = silaframework_pb2_module.Date
        self.__timezone_field = Timezone(silaframework_pb2_module)

    def to_message(self, value: SilaDateType, toplevel_named_data_node: Optional[NamedDataNode] = None) -> SilaDate:
        d, tz = value
        if not isinstance(d, date):
            raise TypeError("Expected a date")

        return self.message_type(
            day=d.day,
            month=d.month,
            year=d.year,
            timezone=self.__timezone_field.to_message(tz),
        )

    def to_native_type(
        self, message: SilaDate, toplevel_named_data_node: Optional[NamedDataNode] = None
    ) -> SilaDateType:
        return SilaDateType(
            date(day=message.day, month=message.month, year=message.year),
            self.__timezone_field.to_native_type(message.timezone),
        )

    @staticmethod
    def from_string(value: str) -> SilaDateType:
        return SilaDateType(date.fromisoformat(value[:10]), Timezone.from_string(value[10:]))
