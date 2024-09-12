import grpc
from grpc import RpcError


class SilaConnectionError(Exception):
    inner_exception: Exception

    def __init__(self, inner_exception: Exception):
        self.inner_exception = inner_exception
        if isinstance(inner_exception, RpcError):
            if inner_exception.code() == grpc.StatusCode.UNAVAILABLE:
                message = "Failed to establish connection to the server"
            else:
                message = f"{inner_exception.code().name} - {inner_exception.details()}"
            message = f"{inner_exception.code().name} - {message}"
        else:
            message = str(inner_exception)
        super().__init__(f"{inner_exception.__class__.__name__}: {message}")
