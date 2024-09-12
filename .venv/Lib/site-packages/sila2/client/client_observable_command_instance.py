from __future__ import annotations

import warnings
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Generic, NamedTuple, Optional, TypeVar
from uuid import UUID

from sila2.client.execution_info_subscription_thread import ExecutionInfoSubscriptionThread
from sila2.client.grpc_stream_subscription import GrpcStreamSubscription
from sila2.client.utils import call_rpc_function
from sila2.framework.command.execution_info import CommandExecutionInfo, CommandExecutionStatus

if TYPE_CHECKING:
    from sila2.client import SilaClient
    from sila2.client.client_observable_command import ClientObservableCommand
    from sila2.client.subscription import Subscription
    from sila2.framework.pb2.SiLAFramework_pb2 import CommandExecutionUUID as SilaCommandExecutionUUID

ResponseType = TypeVar("ResponseType", bound=NamedTuple)
IntermediateResponseType = TypeVar("IntermediateResponseType", bound=NamedTuple)


class ClientObservableCommandInstance(Generic[ResponseType]):
    """
    Represents the execution of an observable command
    """

    _client_command: ClientObservableCommand
    execution_uuid: UUID
    __status: Optional[CommandExecutionStatus]
    __progress: Optional[float]
    estimated_remaining_time: Optional[timedelta]
    lifetime_of_execution: Optional[timedelta]
    __lifetime_of_execution: Optional[timedelta]
    __last_remaining_time_update_timestamp: datetime
    __last_remaining_time_update_duration: Optional[timedelta]
    __info_update_thread: ExecutionInfoSubscriptionThread

    def __init__(
        self,
        parent_client: SilaClient,
        client_command: ClientObservableCommand,
        execution_uuid: UUID,
        lifetime_of_execution: Optional[timedelta] = None,
    ):
        self._parent_client = parent_client
        self._client_command = client_command
        self.__execution_uuid = execution_uuid
        self.__last_remaining_time_update_duration = None
        self.__last_remaining_time_update_timestamp = datetime.now()
        self.__lifetime_of_execution = lifetime_of_execution
        self.__status = None
        self.__progress = None
        self.__info_update_thread = ExecutionInfoSubscriptionThread(
            self._client_command._wrapped_command.fully_qualified_identifier,
            self.execution_uuid,
            getattr(client_command._parent_feature._grpc_stub, f"{client_command._wrapped_command._identifier}_Info")(
                self._get_execution_uuid_message()
            ),
            self,
        )
        self.__info_update_thread.start()

    @property
    def execution_uuid(self) -> UUID:
        """Execution UUID of the represented command instance."""
        return self.__execution_uuid

    @property
    def lifetime_of_execution(self) -> Optional[timedelta]:
        """
        Duration until the SiLA Server is allowed to forget about this command execution (``None``: infinite lifetime)
        """
        return self.__lifetime_of_execution

    def __set_lifetime_of_execution(self, value: Optional[timedelta]) -> None:
        # lifetime is infinite
        if self.lifetime_of_execution is None and value is None:
            return

        # server limited previously unlimited lifetime
        if self.lifetime_of_execution is None and value is not None:
            warnings.warn(
                f"Server shortened previously unconstrained lifetime of observable command instance "
                f"{self.execution_uuid}. Ignoring."
            )
            return

        # server removed lifetime limit
        if value is None:
            return

        # server shortened lifetime
        if value < self.lifetime_of_execution:
            warnings.warn(
                f"Server shortened the lifetime of observable command {self.execution_uuid} from "
                f"{self.lifetime_of_execution} to {value}. Ignoring."
            )
            return

        # server kept or extended lifetime
        self.__lifetime_of_execution = value

    @property
    def estimated_remaining_time(self) -> Optional[timedelta]:
        """Estimated remaining time (``None`` if the SiLA Server has not provided this information)"""
        if self.__last_remaining_time_update_duration is None:
            return None
        remaining = self.__last_remaining_time_update_duration - (
            datetime.now() - self.__last_remaining_time_update_timestamp
        )
        if remaining.total_seconds() < 0:
            return timedelta(0)
        return remaining

    @property
    def status(self) -> Optional[CommandExecutionStatus]:
        """Execution status (``None`` if the SiLA Server has not provided this information)"""
        return self.__status

    @property
    def progress(self) -> Optional[float]:
        """Progress in percent (``None`` if the SiLA Server has not provided this information)"""
        return self.__progress

    @property
    def done(self) -> bool:
        """``True`` if status is either ``finishedSuccessfully`` or ``finishedWithError``"""
        return self.status in (CommandExecutionStatus.finishedSuccessfully, CommandExecutionStatus.finishedWithError)

    def __set_estimated_remaining_time(self, value: Optional[timedelta]) -> None:
        if value is None:
            return
        self.__last_remaining_time_update_timestamp = datetime.now()
        self.__last_remaining_time_update_duration = value

    def _update(self, new_execution_info: CommandExecutionInfo) -> None:
        self.__status = new_execution_info.status
        self.__progress = new_execution_info.progress
        self.__set_estimated_remaining_time(new_execution_info.estimated_remaining_time)
        self.__set_lifetime_of_execution(new_execution_info.updated_lifetime_of_execution)

    def get_responses(self) -> ResponseType:
        """
        Request the command responses

        Returns
        -------
        responses
            Command responses as named tuple

        Raises
        ------
        CommandExecutionNotFinished
            If the command is still running
        SilaError
            If an error occurred during command execution
        """
        rpc_func = getattr(
            self._client_command._parent_feature._grpc_stub,
            f"{self._client_command._wrapped_command._identifier}_Result",
        )
        response_msg = call_rpc_function(
            rpc_func,
            self._get_execution_uuid_message(),
            metadata=None,
            client=self._client_command._parent_feature._parent_client,
            origin=self._client_command._wrapped_command,
        )
        return self._client_command._wrapped_command.responses.to_native_type(response_msg)

    def _get_execution_uuid_message(self) -> SilaCommandExecutionUUID:
        return self._client_command._parent_feature._pb2_module.SiLAFramework__pb2.CommandExecutionUUID(
            value=str(self.execution_uuid)
        )

    def cancel_execution_info_subscription(self) -> None:
        """
        Cancel the subscription to execution information.

        This instance will no longer listen for updates to the command execution status, progress,
        or estimated remaining time.
        """
        self.__info_update_thread.cancel()


class ClientObservableCommandInstanceWithIntermediateResponses(ClientObservableCommandInstance[ResponseType]):
    def subscribe_to_intermediate_responses(self) -> Subscription[IntermediateResponseType]:
        """
        Subscribe to intermediate responses

        Returns
        -------
        intermediate_response_subscription
            Subscription to the intermediate responses
        """
        rpc_func = getattr(
            self._client_command._parent_feature._grpc_stub,
            f"{self._client_command._wrapped_command._identifier}_Intermediate",
        )
        return GrpcStreamSubscription(
            rpc_func(self._get_execution_uuid_message()),
            self._client_command._wrapped_command.intermediate_responses.to_native_type,
            self._parent_client._task_executor,
        )

    def get_intermediate_response(self) -> IntermediateResponseType:
        """
        Request the current intermediate response item

        Returns
        -------
        intermediate_response : NamedTuple
            The current intermediate response

        Notes
        -----
        This is equivalent to subscribing to intermediate response and cancelling the subscription after receiving the
        first item
        """
        with self.subscribe_to_intermediate_responses() as sub:
            return next(sub)
