from typing import Callable, Iterator, TypeVar

import grpc
from grpc import RpcError
from grpc._channel import _MultiThreadedRendezvous

T = TypeVar("T")


class SubscriptionStream(Iterator[T]):
    __wrapped_stream: _MultiThreadedRendezvous
    __converter_func: Callable

    def __init__(self, wrapped_stream: _MultiThreadedRendezvous, converter_func: Callable) -> None:
        self.__wrapped_stream = wrapped_stream
        self.__converter_func = converter_func

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return self.__converter_func(next(self.__wrapped_stream))
        except RpcError as rpc_err:
            if rpc_err.code() == grpc.StatusCode.CANCELLED:
                raise StopIteration()
            raise

    def cancel(self):
        self.__wrapped_stream.cancel()
