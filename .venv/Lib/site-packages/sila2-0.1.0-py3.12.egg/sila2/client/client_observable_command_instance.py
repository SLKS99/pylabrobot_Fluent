from __future__ import annotations

import warnings
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Generic, Optional, TypeVar
from uuid import UUID

from sila2.client.execution_info_subscription_thread import ExecutionInfoSubscriptionThread
from sila2.client.no_intermediate_responses import NoIntermediateResponses
from sila2.client.subscription_stream import SubscriptionStream
from sila2.client.utils import call_rpc_function
from sila2.framework.command.execution_info import CommandExecutionInfo, CommandExecutionStatus

if TYPE_CHECKING:
    from sila2.client.client_observable_command import ClientObservableCommand
    from sila2.pb2_stubs.SiLAFramework_pb2 import CommandExecutionUUID as SilaCommandExecutionUUID

ResultType = TypeVar("ResultType")
IntermediateType = TypeVar("IntermediateType")


class ClientObservableCommandInstance(Generic[IntermediateType, ResultType]):
    _client_command: ClientObservableCommand
    execution_uuid: UUID
    status: Optional[CommandExecutionStatus]
    progress: Optional[float]
    estimated_remaining_time: Optional[timedelta]
    lifetime_of_execution: Optional[timedelta]
    done: bool
    __last_lifetime_update_timestamp: datetime
    __last_lifetime_update_duration: Optional[timedelta]
    __last_remaining_time_update_timestamp: datetime
    __last_remaining_time_update_duration: Optional[timedelta]
    __info_update_thread: ExecutionInfoSubscriptionThread

    def __init__(
        self,
        client_command: ClientObservableCommand,
        execution_uuid: UUID,
        lifetime_of_execution: Optional[timedelta] = None,
    ):
        self._client_command = client_command
        self.execution_uuid = execution_uuid
        self.__last_remaining_time_update_duration = None
        self.__last_remaining_time_update_timestamp = datetime.now()
        self.__last_lifetime_update_duration = None
        self.__last_lifetime_update_timestamp = datetime.now()
        self.lifetime_of_execution = lifetime_of_execution
        self.status = None
        self.progress = None
        self.estimated_remaining_time = None
        self.done = False
        self.__info_update_thread = ExecutionInfoSubscriptionThread(
            self._client_command._wrapped_command.fully_qualified_identifier,
            self.execution_uuid,
            getattr(client_command._parent_feature._grpc_stub, f"{client_command._wrapped_command._identifier}_Info")(
                self.__get_execution_uuid_message()
            ),
            self,
        )
        self.__info_update_thread.start()

    @property
    def lifetime_of_execution(self) -> Optional[timedelta]:
        if self.__last_lifetime_update_duration is None:
            return None
        lifetime = datetime.now() - self.__last_lifetime_update_timestamp + self.__last_lifetime_update_duration
        if lifetime.total_seconds() < 0:
            return timedelta(0)
        return lifetime

    @lifetime_of_execution.setter
    def lifetime_of_execution(self, value: Optional[timedelta]) -> None:
        if self.lifetime_of_execution is None:
            if value is not None:
                warnings.warn(
                    f"Server shortened previously unconstrained lifetime of observable command instance "
                    f"{self.execution_uuid}. Ignoring."
                )
            return
        if value is None:
            warnings.warn("Server did not provide an updated lifetime of execution. Keeping the previous one.")
            return
        if value < self.lifetime_of_execution:
            warnings.warn(
                f"Server shortened the lifetime of observable command {self.execution_uuid} from "
                f"{self.lifetime_of_execution} to {value}. Ignoring."
            )
            return
        self.__last_lifetime_update_duration = value
        self.__last_lifetime_update_timestamp = datetime.now()

    @property
    def estimated_remaining_time(self) -> Optional[timedelta]:
        if self.__last_remaining_time_update_duration is None:
            return None
        remaining = self.__last_remaining_time_update_duration - (
            datetime.now() - self.__last_remaining_time_update_timestamp
        )
        if remaining.total_seconds() < 0:
            return timedelta(0)
        return remaining

    @estimated_remaining_time.setter
    def estimated_remaining_time(self, value: Optional[timedelta]) -> None:
        if value is None:
            return
        self.__last_remaining_time_update_timestamp = datetime.now()
        self.__last_remaining_time_update_duration = value

    def _update(self, new_execution_info: CommandExecutionInfo) -> None:
        self.status = new_execution_info.status
        self.progress = new_execution_info.progress
        self.estimated_remaining_time = new_execution_info.estimated_remaining_time
        self.lifetime_of_execution = new_execution_info.updated_lifetime_of_execution
        if new_execution_info.status in (
            CommandExecutionStatus.finishedSuccessfully,
            CommandExecutionStatus.finishedWithError,
        ):
            self.done = True

    def subscribe_intermediate_responses(self) -> SubscriptionStream[IntermediateType]:
        if self._client_command._wrapped_command.intermediate_responses is None:
            raise NoIntermediateResponses(
                f"Command {self._client_command._wrapped_command._identifier} has no intermediate responses"
            )

        rpc_func = getattr(
            self._client_command._parent_feature._grpc_stub,
            f"{self._client_command._wrapped_command._identifier}_Intermediate",
        )
        return SubscriptionStream(
            rpc_func(self.__get_execution_uuid_message()),
            self._client_command._wrapped_command.intermediate_responses.to_native_type,
        )

    def get_responses(self) -> ResultType:
        rpc_func = getattr(
            self._client_command._parent_feature._grpc_stub,
            f"{self._client_command._wrapped_command._identifier}_Result",
        )
        response_msg = call_rpc_function(
            rpc_func,
            self.__get_execution_uuid_message(),
            metadata=None,
            client=self._client_command._parent_feature._parent_client,
            origin=self._client_command._wrapped_command,
        )
        # response_msg = rpc_func(self.__get_execution_uuid_message())
        return self._client_command._wrapped_command.responses.to_native_type(response_msg)

    def __get_execution_uuid_message(self) -> SilaCommandExecutionUUID:
        return self._client_command._parent_feature._pb2_module.SiLAFramework__pb2.CommandExecutionUUID(
            value=str(self.execution_uuid)
        )
