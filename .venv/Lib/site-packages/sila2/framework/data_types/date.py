from __future__ import annotations

from datetime import date, tzinfo
from typing import TYPE_CHECKING, Iterable, NamedTuple, Optional

from sila2.framework.abc.data_type import DataType
from sila2.framework.abc.named_data_node import NamedDataNode
from sila2.framework.data_types.timezone import Timezone
from sila2.framework.errors.validation_error import ValidationError
from sila2.framework.pb2 import SiLAFramework_pb2
from sila2.framework.pb2.SiLAFramework_pb2 import Date as SilaDate

if TYPE_CHECKING:
    from sila2.client import ClientMetadataInstance


class SilaDateType(NamedTuple):
    date: date
    """Date"""
    timezone: tzinfo
    """Timezone"""


class Date(DataType[SilaDate, SilaDateType]):
    message_type = SiLAFramework_pb2.Date

    def to_message(
        self,
        sila_date: SilaDateType,
        *,
        toplevel_named_data_node: Optional[NamedDataNode] = None,
        metadata: Optional[Iterable[ClientMetadataInstance]] = None,
    ) -> SilaDate:
        if sila_date.timezone.utcoffset(None) is None:
            raise ValueError(
                "The given timezone is ambiguous. "
                "Please provide an explicit UTC offset, e.g. by using `datetime.timezone(datetime.timedelta(...))`"
            )

        return SiLAFramework_pb2.Date(
            day=sila_date.date.day,
            month=sila_date.date.month,
            year=sila_date.date.year,
            timezone=Timezone().to_message(sila_date.timezone.utcoffset(None)),
        )

    def to_native_type(
        self, message: SilaDate, toplevel_named_data_node: Optional[NamedDataNode] = None
    ) -> SilaDateType:
        if not message.HasField("timezone"):
            raise ValidationError("Date type is missing required field 'timezone'")
        return SilaDateType(
            date(day=message.day, month=message.month, year=message.year),
            Timezone().to_native_type(message.timezone),
        )

    @staticmethod
    def from_string(value: str) -> SilaDateType:
        return SilaDateType(date.fromisoformat(value[:10]), Timezone.from_string(value[10:]))
