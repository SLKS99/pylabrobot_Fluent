from __future__ import annotations

from abc import ABC
from datetime import date, datetime, time, timezone
from typing import Any, Callable, Tuple, Union

from sila2.framework.abc.constraint import Constraint
from sila2.framework.data_types.date import Date
from sila2.framework.data_types.integer import Integer
from sila2.framework.data_types.real import Real
from sila2.framework.data_types.string import String
from sila2.framework.data_types.time import Time
from sila2.framework.data_types.timestamp import Timestamp


class ComparisonConstraint(Constraint, ABC):
    comparison_operator: Callable[[Any, Any], bool]
    base_type: Union[String, Integer, Real, Date, Time, Timestamp]
    parsed_value: Union[str, int, float, datetime]
    value: str

    def __init__(
        self,
        base_type: Union[String, Integer, Real, Date, Time, Timestamp],
        comparison_operator: Callable[[Any, Any], bool],
        value: str,
    ):
        self.base_type = base_type
        self.comparison_operator = comparison_operator
        self.value = value
        self.parsed_value = self._parse_value_from_string(value)

    def validate(self, value: Union[str, int, float, Tuple[date, timezone], time, datetime]):
        parsed_value = self._convert_value_for_comparison(value)
        return self.comparison_operator(self.parsed_value, parsed_value)

    def _convert_value_for_comparison(self, value: Union[str, int, float, Tuple[date, timezone], time, datetime]):
        if isinstance(self.base_type, (String, Integer, Real, Timestamp)):
            return value
        if isinstance(self.base_type, Date):
            d, tz = value
            return datetime(year=d.year, month=d.month, day=d.day, tzinfo=tz)
        if isinstance(self.base_type, Time):
            return datetime(
                year=2000,
                month=1,
                day=1,
                hour=value.hour,
                minute=value.minute,
                second=value.second,
                tzinfo=value.tzinfo,
            )
        else:
            raise NotImplementedError  # should never happen

    def _parse_value_from_string(self, value: str) -> Union[str, int, float, datetime]:
        if isinstance(self.base_type, String):
            return value
        if isinstance(self.base_type, Integer):
            return int(value)
        if isinstance(self.base_type, Real):
            return float(value)
        if isinstance(self.base_type, Date):
            d, tz = Date.from_string(value)
            return datetime(year=d.year, month=d.month, day=d.day, tzinfo=tz)
        if isinstance(self.base_type, Time):
            t = Time.from_string(value)
            return datetime(year=2000, month=1, day=1, hour=t.hour, minute=t.minute, second=t.second, tzinfo=t.tzinfo)
        if isinstance(self.base_type, Timestamp):
            return Timestamp.from_string(value)
        else:
            raise NotImplementedError  # should never happen

    def __repr__(self) -> str:
        if isinstance(self.base_type, (Integer, Real)):
            return f"{self.__class__.__name__}({self.parsed_value})"
        return f"{self.__class__.__name__}({self.value!r})"
