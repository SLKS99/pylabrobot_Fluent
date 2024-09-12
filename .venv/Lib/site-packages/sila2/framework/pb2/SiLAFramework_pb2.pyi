from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class String(_message.Message):
    __slots__ = ["value"]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: str
    def __init__(self, value: _Optional[str] = ...) -> None: ...

class Integer(_message.Message):
    __slots__ = ["value"]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: int
    def __init__(self, value: _Optional[int] = ...) -> None: ...

class Real(_message.Message):
    __slots__ = ["value"]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: float
    def __init__(self, value: _Optional[float] = ...) -> None: ...

class Boolean(_message.Message):
    __slots__ = ["value"]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: bool
    def __init__(self, value: bool = ...) -> None: ...

class Binary(_message.Message):
    __slots__ = ["value", "binaryTransferUUID"]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    BINARYTRANSFERUUID_FIELD_NUMBER: _ClassVar[int]
    value: bytes
    binaryTransferUUID: str
    def __init__(self, value: _Optional[bytes] = ..., binaryTransferUUID: _Optional[str] = ...) -> None: ...

class Date(_message.Message):
    __slots__ = ["day", "month", "year", "timezone"]
    DAY_FIELD_NUMBER: _ClassVar[int]
    MONTH_FIELD_NUMBER: _ClassVar[int]
    YEAR_FIELD_NUMBER: _ClassVar[int]
    TIMEZONE_FIELD_NUMBER: _ClassVar[int]
    day: int
    month: int
    year: int
    timezone: Timezone
    def __init__(self, day: _Optional[int] = ..., month: _Optional[int] = ..., year: _Optional[int] = ..., timezone: _Optional[_Union[Timezone, _Mapping]] = ...) -> None: ...

class Time(_message.Message):
    __slots__ = ["second", "minute", "hour", "timezone", "millisecond"]
    SECOND_FIELD_NUMBER: _ClassVar[int]
    MINUTE_FIELD_NUMBER: _ClassVar[int]
    HOUR_FIELD_NUMBER: _ClassVar[int]
    TIMEZONE_FIELD_NUMBER: _ClassVar[int]
    MILLISECOND_FIELD_NUMBER: _ClassVar[int]
    second: int
    minute: int
    hour: int
    timezone: Timezone
    millisecond: int
    def __init__(self, second: _Optional[int] = ..., minute: _Optional[int] = ..., hour: _Optional[int] = ..., timezone: _Optional[_Union[Timezone, _Mapping]] = ..., millisecond: _Optional[int] = ...) -> None: ...

class Timestamp(_message.Message):
    __slots__ = ["second", "minute", "hour", "day", "month", "year", "timezone", "millisecond"]
    SECOND_FIELD_NUMBER: _ClassVar[int]
    MINUTE_FIELD_NUMBER: _ClassVar[int]
    HOUR_FIELD_NUMBER: _ClassVar[int]
    DAY_FIELD_NUMBER: _ClassVar[int]
    MONTH_FIELD_NUMBER: _ClassVar[int]
    YEAR_FIELD_NUMBER: _ClassVar[int]
    TIMEZONE_FIELD_NUMBER: _ClassVar[int]
    MILLISECOND_FIELD_NUMBER: _ClassVar[int]
    second: int
    minute: int
    hour: int
    day: int
    month: int
    year: int
    timezone: Timezone
    millisecond: int
    def __init__(self, second: _Optional[int] = ..., minute: _Optional[int] = ..., hour: _Optional[int] = ..., day: _Optional[int] = ..., month: _Optional[int] = ..., year: _Optional[int] = ..., timezone: _Optional[_Union[Timezone, _Mapping]] = ..., millisecond: _Optional[int] = ...) -> None: ...

class Timezone(_message.Message):
    __slots__ = ["hours", "minutes"]
    HOURS_FIELD_NUMBER: _ClassVar[int]
    MINUTES_FIELD_NUMBER: _ClassVar[int]
    hours: int
    minutes: int
    def __init__(self, hours: _Optional[int] = ..., minutes: _Optional[int] = ...) -> None: ...

class Any(_message.Message):
    __slots__ = ["type", "payload"]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    type: str
    payload: bytes
    def __init__(self, type: _Optional[str] = ..., payload: _Optional[bytes] = ...) -> None: ...

class Duration(_message.Message):
    __slots__ = ["seconds", "nanos"]
    SECONDS_FIELD_NUMBER: _ClassVar[int]
    NANOS_FIELD_NUMBER: _ClassVar[int]
    seconds: int
    nanos: int
    def __init__(self, seconds: _Optional[int] = ..., nanos: _Optional[int] = ...) -> None: ...

class CommandExecutionUUID(_message.Message):
    __slots__ = ["value"]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: str
    def __init__(self, value: _Optional[str] = ...) -> None: ...

class CommandConfirmation(_message.Message):
    __slots__ = ["commandExecutionUUID", "lifetimeOfExecution"]
    COMMANDEXECUTIONUUID_FIELD_NUMBER: _ClassVar[int]
    LIFETIMEOFEXECUTION_FIELD_NUMBER: _ClassVar[int]
    commandExecutionUUID: CommandExecutionUUID
    lifetimeOfExecution: Duration
    def __init__(self, commandExecutionUUID: _Optional[_Union[CommandExecutionUUID, _Mapping]] = ..., lifetimeOfExecution: _Optional[_Union[Duration, _Mapping]] = ...) -> None: ...

class ExecutionInfo(_message.Message):
    __slots__ = ["commandStatus", "progressInfo", "estimatedRemainingTime", "updatedLifetimeOfExecution"]
    class CommandStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        waiting: _ClassVar[ExecutionInfo.CommandStatus]
        running: _ClassVar[ExecutionInfo.CommandStatus]
        finishedSuccessfully: _ClassVar[ExecutionInfo.CommandStatus]
        finishedWithError: _ClassVar[ExecutionInfo.CommandStatus]
    waiting: ExecutionInfo.CommandStatus
    running: ExecutionInfo.CommandStatus
    finishedSuccessfully: ExecutionInfo.CommandStatus
    finishedWithError: ExecutionInfo.CommandStatus
    COMMANDSTATUS_FIELD_NUMBER: _ClassVar[int]
    PROGRESSINFO_FIELD_NUMBER: _ClassVar[int]
    ESTIMATEDREMAININGTIME_FIELD_NUMBER: _ClassVar[int]
    UPDATEDLIFETIMEOFEXECUTION_FIELD_NUMBER: _ClassVar[int]
    commandStatus: ExecutionInfo.CommandStatus
    progressInfo: Real
    estimatedRemainingTime: Duration
    updatedLifetimeOfExecution: Duration
    def __init__(self, commandStatus: _Optional[_Union[ExecutionInfo.CommandStatus, str]] = ..., progressInfo: _Optional[_Union[Real, _Mapping]] = ..., estimatedRemainingTime: _Optional[_Union[Duration, _Mapping]] = ..., updatedLifetimeOfExecution: _Optional[_Union[Duration, _Mapping]] = ...) -> None: ...

class SiLAError(_message.Message):
    __slots__ = ["validationError", "definedExecutionError", "undefinedExecutionError", "frameworkError"]
    VALIDATIONERROR_FIELD_NUMBER: _ClassVar[int]
    DEFINEDEXECUTIONERROR_FIELD_NUMBER: _ClassVar[int]
    UNDEFINEDEXECUTIONERROR_FIELD_NUMBER: _ClassVar[int]
    FRAMEWORKERROR_FIELD_NUMBER: _ClassVar[int]
    validationError: ValidationError
    definedExecutionError: DefinedExecutionError
    undefinedExecutionError: UndefinedExecutionError
    frameworkError: FrameworkError
    def __init__(self, validationError: _Optional[_Union[ValidationError, _Mapping]] = ..., definedExecutionError: _Optional[_Union[DefinedExecutionError, _Mapping]] = ..., undefinedExecutionError: _Optional[_Union[UndefinedExecutionError, _Mapping]] = ..., frameworkError: _Optional[_Union[FrameworkError, _Mapping]] = ...) -> None: ...

class ValidationError(_message.Message):
    __slots__ = ["parameter", "message"]
    PARAMETER_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    parameter: str
    message: str
    def __init__(self, parameter: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class DefinedExecutionError(_message.Message):
    __slots__ = ["errorIdentifier", "message"]
    ERRORIDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    errorIdentifier: str
    message: str
    def __init__(self, errorIdentifier: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class UndefinedExecutionError(_message.Message):
    __slots__ = ["message"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...

class FrameworkError(_message.Message):
    __slots__ = ["errorType", "message"]
    class ErrorType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        COMMAND_EXECUTION_NOT_ACCEPTED: _ClassVar[FrameworkError.ErrorType]
        INVALID_COMMAND_EXECUTION_UUID: _ClassVar[FrameworkError.ErrorType]
        COMMAND_EXECUTION_NOT_FINISHED: _ClassVar[FrameworkError.ErrorType]
        INVALID_METADATA: _ClassVar[FrameworkError.ErrorType]
        NO_METADATA_ALLOWED: _ClassVar[FrameworkError.ErrorType]
    COMMAND_EXECUTION_NOT_ACCEPTED: FrameworkError.ErrorType
    INVALID_COMMAND_EXECUTION_UUID: FrameworkError.ErrorType
    COMMAND_EXECUTION_NOT_FINISHED: FrameworkError.ErrorType
    INVALID_METADATA: FrameworkError.ErrorType
    NO_METADATA_ALLOWED: FrameworkError.ErrorType
    ERRORTYPE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    errorType: FrameworkError.ErrorType
    message: str
    def __init__(self, errorType: _Optional[_Union[FrameworkError.ErrorType, str]] = ..., message: _Optional[str] = ...) -> None: ...
