from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Iterable, Optional

from sila2.framework.abc.data_type import DataType
from sila2.framework.abc.named_data_node import NamedDataNode
from sila2.framework.data_types.timezone import Timezone
from sila2.framework.errors.validation_error import ValidationError
from sila2.framework.pb2 import SiLAFramework_pb2
from sila2.framework.pb2.SiLAFramework_pb2 import Timestamp as SilaTimestamp

if TYPE_CHECKING:
    from sila2.client import ClientMetadataInstance


class Timestamp(DataType[SilaTimestamp, datetime]):
    message_type = SiLAFramework_pb2.Timestamp

    def to_message(
        self,
        dt: datetime,
        *,
        toplevel_named_data_node: Optional[NamedDataNode] = None,
        metadata: Optional[Iterable[ClientMetadataInstance]] = None,
    ) -> SilaTimestamp:
        if not isinstance(dt, datetime):
            raise TypeError("Expected a datetime")
        if dt.tzinfo is None:
            raise ValueError("No timezone provided")

        return SiLAFramework_pb2.Timestamp(
            year=dt.year,
            month=dt.month,
            day=dt.day,
            hour=dt.hour,
            minute=dt.minute,
            second=dt.second,
            millisecond=dt.microsecond // 1000,
            timezone=Timezone().to_message(dt.utcoffset()),
        )

    def to_native_type(
        self, message: SilaTimestamp, toplevel_named_data_node: Optional[NamedDataNode] = None
    ) -> datetime:
        if not message.HasField("timezone"):
            raise ValidationError("Date type is missing required field 'timezone'")
        return datetime(
            year=message.year,
            month=message.month,
            day=message.day,
            hour=message.hour,
            minute=message.minute,
            second=message.second,
            microsecond=message.millisecond * 1000,
            tzinfo=Timezone().to_native_type(message.timezone),
        )

    @staticmethod
    def from_string(value: str) -> datetime:
        if len(value) not in (20, 25):
            raise ValueError(
                f"Invalid timestamp format: '{value}'. "
                f"Must be 'YYYY-MM-DDTHH:MM:SS' plus timezone as 'Z', '-HH:MM' or '+HH:MM'"
            )
        dt = datetime.fromisoformat(value[:19])
        tz = Timezone.from_string(value[19:])
        return datetime(
            year=dt.year, month=dt.month, day=dt.day, hour=dt.hour, minute=dt.minute, second=dt.second, tzinfo=tz
        )
