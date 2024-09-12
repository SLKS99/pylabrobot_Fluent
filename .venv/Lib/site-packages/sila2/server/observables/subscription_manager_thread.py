from __future__ import annotations

import logging
import uuid
from queue import Queue
from threading import Thread
from typing import TYPE_CHECKING, Callable, Generic, List, Optional, TypeVar, Union

from sila2.framework.fully_qualified_identifier import FullyQualifiedCommandIdentifier, FullyQualifiedPropertyIdentifier
from sila2.server.observables.stream import Stream

if TYPE_CHECKING:
    from grpc import ServicerContext

T = TypeVar("T")


class SubscriptionManagerThread(Thread, Generic[T]):
    __producer_stream: Stream[T]
    __subscriber_streams: List[Stream[T]]
    __converter_func: Callable
    __last_item: Optional[T]

    def __init__(
        self,
        origin_identifier: Union[FullyQualifiedPropertyIdentifier, FullyQualifiedCommandIdentifier],
        producer_queue: Queue[T],
        converter_func: Callable,
    ):
        super().__init__(name=f"{self.__class__.__name__}-{origin_identifier}")
        _, _, feature_id, _, _, target_id = origin_identifier.split("/")
        self.__target_id = f"{feature_id}.{target_id}"
        self.__producer_stream = Stream.from_queue(producer_queue, name=f"producer-stream-{self.__target_id}")
        self.__subscriber_streams = []
        self.__converter_func = converter_func
        self.__last_item = None

        self.logger = logging.getLogger(f"{self.__class__.__name__}[{feature_id}.{target_id}]")

    def add_subscription(self, context: ServicerContext) -> Stream[T]:
        s = Stream(name=f"subscription-stream-{self.__target_id}-{uuid.uuid4()}")

        # send last item so clients receive the current status immediately
        if self.__last_item is not None:
            s.put(self.__last_item)

        context.add_callback(lambda: self.cancel_subscription(s))

        self.__subscriber_streams.append(s)
        return s

    def cancel_subscription(self, subscription: Stream[T]):
        if subscription.is_alive:
            subscription.cancel()
        self.__subscriber_streams.remove(subscription)

    def run(self):
        for item in self.__producer_stream:
            self.logger.info(f"Received item, forwarding to all subscribers: {item!r}")
            if isinstance(item, BaseException):
                self.__last_item = item
            else:
                self.__last_item = self.__converter_func(item)
            for subscriber in self.__subscriber_streams:
                subscriber.put(self.__last_item)

        self.__cancel_all_subscriptions()

    def __cancel_all_subscriptions(self) -> None:
        for s in self.__subscriber_streams:
            s.cancel()

    def cancel_producer(self):
        self.__producer_stream.cancel()
