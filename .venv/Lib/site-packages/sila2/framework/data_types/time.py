from __future__ import annotations

from datetime import time
from typing import TYPE_CHECKING, Iterable, Optional

from sila2.framework.abc.data_type import DataType
from sila2.framework.abc.named_data_node import NamedDataNode
from sila2.framework.data_types.timezone import Timezone
from sila2.framework.errors.validation_error import ValidationError
from sila2.framework.pb2 import SiLAFramework_pb2
from sila2.framework.pb2.SiLAFramework_pb2 import Time as SilaTime

if TYPE_CHECKING:
    from sila2.client import ClientMetadataInstance


class Time(DataType[SilaTime, time]):
    message_type = SiLAFramework_pb2.Time

    def to_message(
        self,
        t: time,
        *,
        toplevel_named_data_node: Optional[NamedDataNode] = None,
        metadata: Optional[Iterable[ClientMetadataInstance]] = None,
    ) -> SilaTime:
        if not isinstance(t, time):
            raise TypeError("Expected a time")
        if t.tzinfo is None:
            raise ValueError("No timezone provided")
        if t.tzinfo.utcoffset(None) is None:
            raise ValueError(
                "The given timezone is ambiguous. "
                "Please provide an explicit UTC offset, e.g. by using `datetime.timezone(datetime.timedelta(...))`"
            )

        return SiLAFramework_pb2.Time(
            hour=t.hour,
            minute=t.minute,
            second=t.second,
            millisecond=t.microsecond // 1000,
            timezone=Timezone().to_message(t.tzinfo.utcoffset(None)),
        )

    def to_native_type(self, message: SilaTime, toplevel_named_data_node: Optional[NamedDataNode] = None) -> time:
        if not message.HasField("timezone"):
            raise ValidationError("Date type is missing required field 'timezone'")
        return time(
            hour=message.hour,
            minute=message.minute,
            second=message.second,
            microsecond=message.millisecond * 1000,
            tzinfo=Timezone().to_native_type(message.timezone),
        )

    @staticmethod
    def from_string(value: str) -> time:
        t = time.fromisoformat(value[:8])
        tz = Timezone.from_string(value[8:])
        return time(hour=t.hour, minute=t.minute, second=t.second, tzinfo=tz)
