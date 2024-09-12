import functools
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from typing import Any, Callable, Iterable, Optional, TypeVar

from grpc import RpcError
from grpc._channel import _MultiThreadedRendezvous

from sila2.client.subscription import Subscription

T = TypeVar("T")


class GrpcStreamSubscription(Subscription[T]):
    def __init__(
        self,
        wrapped_stream: _MultiThreadedRendezvous,
        converter_func: Callable[[Any], T],
        executor: ThreadPoolExecutor,
        error_converter: Optional[Callable[[BaseException], BaseException]] = None,
        callbacks: Iterable[Callable[[T], Any]] = (),
    ) -> None:
        super().__init__()
        self.__wrapped_stream = wrapped_stream
        self.__converter_func = converter_func
        self.__executor = executor
        self.__queue = Queue()
        self.__cancelled = False
        self.__error_converter = error_converter

        def looped_func():
            while True:
                try:
                    next_message = next(self.__wrapped_stream)
                except (RpcError, StopIteration) as ex:
                    self.__queue.put(ex)
                    break

                new_item = self.__converter_func(next_message)
                self.__queue.put(new_item)
                for callback in self.callbacks:
                    self.__executor.submit(functools.partial(callback, new_item))

        for callback in callbacks:
            self.add_callback(callback)
        executor.submit(looped_func)

    def __next__(self) -> T:
        item = self.__queue.get()
        if isinstance(item, StopIteration):
            raise item
        if isinstance(item, BaseException):
            if self.__error_converter is None:
                raise item
            raise self.__error_converter(item)
        return item

    def cancel(self):
        self.__wrapped_stream.cancel()
        self.__queue.put(StopIteration())
        self.__cancelled = True

    @property
    def is_cancelled(self) -> bool:
        return self.__cancelled
