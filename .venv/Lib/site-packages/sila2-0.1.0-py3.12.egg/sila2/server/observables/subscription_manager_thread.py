from __future__ import annotations

from queue import Queue
from threading import Thread
from typing import Callable, Generic, List, Optional, TypeVar

from sila2.framework.fully_qualified_identifier import FullyQualifiedIdentifier
from sila2.server.observables.stream import Stream

T = TypeVar("T")


class SubscriptionManagerThread(Thread, Generic[T]):
    __producer_stream: Stream[T]
    __subscriber_streams: List[Stream[T]]
    __converter_func: Callable
    __last_item: Optional[T]

    def __init__(self, origin_identifier: FullyQualifiedIdentifier, producer_queue: Queue[T], converter_func: Callable):
        super().__init__(name=f"{self.__class__.__name__}-{origin_identifier}")
        self.__producer_stream = Stream.from_queue(producer_queue)
        self.__subscriber_streams = []
        self.__converter_func = converter_func
        self.__last_item = None

    def add_subscription(self) -> Stream[T]:
        s = Stream()

        # send last item so clients receive the current status immediately
        if self.__last_item is not None:
            s.put(self.__last_item)

        self.__subscriber_streams.append(s)
        return s

    def run(self):
        for item in self.__producer_stream:
            self.__last_item = self.__converter_func(item)
            for subscriber in self.__subscriber_streams:
                subscriber.put(self.__last_item)

        self.__cancel_all_subscriptions()

    def __cancel_all_subscriptions(self) -> None:
        for s in self.__subscriber_streams:
            s.cancel()

    def cancel_producer(self):
        self.__producer_stream.cancel()
