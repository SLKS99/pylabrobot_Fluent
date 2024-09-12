import SiLAFramework_pb2 as _SiLAFramework_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CreateBinaryRequest(_message.Message):
    __slots__ = ["binarySize", "chunkCount", "parameterIdentifier"]
    BINARYSIZE_FIELD_NUMBER: _ClassVar[int]
    CHUNKCOUNT_FIELD_NUMBER: _ClassVar[int]
    PARAMETERIDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    binarySize: int
    chunkCount: int
    parameterIdentifier: str
    def __init__(self, binarySize: _Optional[int] = ..., chunkCount: _Optional[int] = ..., parameterIdentifier: _Optional[str] = ...) -> None: ...

class CreateBinaryResponse(_message.Message):
    __slots__ = ["binaryTransferUUID", "lifetimeOfBinary"]
    BINARYTRANSFERUUID_FIELD_NUMBER: _ClassVar[int]
    LIFETIMEOFBINARY_FIELD_NUMBER: _ClassVar[int]
    binaryTransferUUID: str
    lifetimeOfBinary: _SiLAFramework_pb2.Duration
    def __init__(self, binaryTransferUUID: _Optional[str] = ..., lifetimeOfBinary: _Optional[_Union[_SiLAFramework_pb2.Duration, _Mapping]] = ...) -> None: ...

class UploadChunkRequest(_message.Message):
    __slots__ = ["binaryTransferUUID", "chunkIndex", "payload"]
    BINARYTRANSFERUUID_FIELD_NUMBER: _ClassVar[int]
    CHUNKINDEX_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    binaryTransferUUID: str
    chunkIndex: int
    payload: bytes
    def __init__(self, binaryTransferUUID: _Optional[str] = ..., chunkIndex: _Optional[int] = ..., payload: _Optional[bytes] = ...) -> None: ...

class UploadChunkResponse(_message.Message):
    __slots__ = ["binaryTransferUUID", "chunkIndex", "lifetimeOfBinary"]
    BINARYTRANSFERUUID_FIELD_NUMBER: _ClassVar[int]
    CHUNKINDEX_FIELD_NUMBER: _ClassVar[int]
    LIFETIMEOFBINARY_FIELD_NUMBER: _ClassVar[int]
    binaryTransferUUID: str
    chunkIndex: int
    lifetimeOfBinary: _SiLAFramework_pb2.Duration
    def __init__(self, binaryTransferUUID: _Optional[str] = ..., chunkIndex: _Optional[int] = ..., lifetimeOfBinary: _Optional[_Union[_SiLAFramework_pb2.Duration, _Mapping]] = ...) -> None: ...

class DeleteBinaryRequest(_message.Message):
    __slots__ = ["binaryTransferUUID"]
    BINARYTRANSFERUUID_FIELD_NUMBER: _ClassVar[int]
    binaryTransferUUID: str
    def __init__(self, binaryTransferUUID: _Optional[str] = ...) -> None: ...

class DeleteBinaryResponse(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class GetBinaryInfoRequest(_message.Message):
    __slots__ = ["binaryTransferUUID"]
    BINARYTRANSFERUUID_FIELD_NUMBER: _ClassVar[int]
    binaryTransferUUID: str
    def __init__(self, binaryTransferUUID: _Optional[str] = ...) -> None: ...

class GetBinaryInfoResponse(_message.Message):
    __slots__ = ["binarySize", "lifetimeOfBinary"]
    BINARYSIZE_FIELD_NUMBER: _ClassVar[int]
    LIFETIMEOFBINARY_FIELD_NUMBER: _ClassVar[int]
    binarySize: int
    lifetimeOfBinary: _SiLAFramework_pb2.Duration
    def __init__(self, binarySize: _Optional[int] = ..., lifetimeOfBinary: _Optional[_Union[_SiLAFramework_pb2.Duration, _Mapping]] = ...) -> None: ...

class GetChunkRequest(_message.Message):
    __slots__ = ["binaryTransferUUID", "offset", "length"]
    BINARYTRANSFERUUID_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    binaryTransferUUID: str
    offset: int
    length: int
    def __init__(self, binaryTransferUUID: _Optional[str] = ..., offset: _Optional[int] = ..., length: _Optional[int] = ...) -> None: ...

class GetChunkResponse(_message.Message):
    __slots__ = ["binaryTransferUUID", "offset", "payload", "lifetimeOfBinary"]
    BINARYTRANSFERUUID_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    LIFETIMEOFBINARY_FIELD_NUMBER: _ClassVar[int]
    binaryTransferUUID: str
    offset: int
    payload: bytes
    lifetimeOfBinary: _SiLAFramework_pb2.Duration
    def __init__(self, binaryTransferUUID: _Optional[str] = ..., offset: _Optional[int] = ..., payload: _Optional[bytes] = ..., lifetimeOfBinary: _Optional[_Union[_SiLAFramework_pb2.Duration, _Mapping]] = ...) -> None: ...

class BinaryTransferError(_message.Message):
    __slots__ = ["errorType", "message"]
    class ErrorType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        INVALID_BINARY_TRANSFER_UUID: _ClassVar[BinaryTransferError.ErrorType]
        BINARY_UPLOAD_FAILED: _ClassVar[BinaryTransferError.ErrorType]
        BINARY_DOWNLOAD_FAILED: _ClassVar[BinaryTransferError.ErrorType]
    INVALID_BINARY_TRANSFER_UUID: BinaryTransferError.ErrorType
    BINARY_UPLOAD_FAILED: BinaryTransferError.ErrorType
    BINARY_DOWNLOAD_FAILED: BinaryTransferError.ErrorType
    ERRORTYPE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    errorType: BinaryTransferError.ErrorType
    message: str
    def __init__(self, errorType: _Optional[_Union[BinaryTransferError.ErrorType, str]] = ..., message: _Optional[str] = ...) -> None: ...
