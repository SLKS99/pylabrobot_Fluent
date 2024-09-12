from __future__ import annotations

import logging
from datetime import timedelta
from queue import Queue
from typing import Generic, Optional, TypeVar
from uuid import UUID

from sila2.framework import CommandExecutionInfo, CommandExecutionStatus


class ObservableCommandInstance:
    """Instance of a currently running observable command. Provides means to update the execution information."""

    def __init__(
        self,
        execution_uuid: UUID,
        execution_info_queue: Queue[CommandExecutionInfo],
        logger: logging.Logger,
        lifetime_of_execution: Optional[timedelta],
    ):
        self.__execution_uuid = execution_uuid
        self.__progress: Optional[float] = None
        self.__estimated_remaining_time: Optional[timedelta] = None
        self.__status: CommandExecutionStatus = CommandExecutionStatus.waiting
        self.__lifetime_of_execution = lifetime_of_execution
        self.__info_queue: Queue[CommandExecutionInfo] = execution_info_queue
        self.__update_execution_info()  # send first update
        self.__logger = logger

    def begin_execution(self) -> None:
        """
        Observable commands start with the status ``waiting``.
        Use this method to set the status to ``running``.
        This is done automatically if the progress is set to a number greater than 0.
        """
        self.__status = CommandExecutionStatus.running
        self.__update_execution_info()

    @property
    def progress(self) -> Optional[float]:
        """
        Command execution progress.
        Must be ``None``, or a number between 0 and 1.
        Clients are notified about updates.
        """
        return self.__progress

    @property
    def execution_uuid(self) -> UUID:
        """Command Execution UUID of this command execution instance."""
        return self.__execution_uuid

    @progress.setter
    def progress(self, progress: float) -> None:
        if not isinstance(progress, (int, float)):
            raise TypeError(f"Expected an int or float, got {progress}")
        if progress < 0 or progress > 1:
            raise ValueError("Progress must be between 0 and 1")
        if progress > 0:
            self.__status = CommandExecutionStatus.running
        self.__progress = progress
        self.__update_execution_info()

    @property
    def estimated_remaining_time(self) -> Optional[timedelta]:
        """Command execution progress. Must be ``None``, or a positive timedelta. Clients are notified about updates."""
        return self.__estimated_remaining_time

    @estimated_remaining_time.setter
    def estimated_remaining_time(self, estimated_remaining_time: timedelta) -> None:
        if not isinstance(estimated_remaining_time, timedelta):
            raise TypeError(f"Expected a datetime.timedelta, got {estimated_remaining_time}")
        if estimated_remaining_time.total_seconds() < 0:
            raise ValueError("Estimated remaining time cannot be negative")
        self.__estimated_remaining_time = estimated_remaining_time
        self.__update_execution_info()

    @property
    def lifetime_of_execution(self) -> Optional[timedelta]:
        """Lifetime of the command execution. Must be ``None``, or a positive timedelta. Clients are notified about
        updates.
        """
        return self.__lifetime_of_execution

    @lifetime_of_execution.setter
    def lifetime_of_execution(self, lifetime_of_execution: timedelta) -> None:
        if not isinstance(lifetime_of_execution, timedelta):
            raise TypeError(f"Expected a datetime.timedelta, got {lifetime_of_execution}")
        if lifetime_of_execution.total_seconds() < 0:
            raise ValueError("Lifetime of execution cannot be negative")
        if self.__lifetime_of_execution is not None and lifetime_of_execution < self.__lifetime_of_execution:
            self.__logger.warning(
                f"Lifetime of execution cannot be decreased! Using previous lifetime {self.__lifetime_of_execution} "
                f"instead of {lifetime_of_execution}."
            )
        else:
            self.__lifetime_of_execution = lifetime_of_execution
        self.__update_execution_info()

    def __update_execution_info(self) -> None:
        self.__info_queue.put(
            CommandExecutionInfo(
                self.__status, self.__progress, self.__estimated_remaining_time, self.__lifetime_of_execution
            )
        )


IntermediateResponseType = TypeVar("IntermediateResponseType")


class ObservableCommandInstanceWithIntermediateResponses(ObservableCommandInstance, Generic[IntermediateResponseType]):
    """
    Instance of a currently running observable command.
    Provides means to update the execution information and send intermediate responses.
    """

    def __init__(
        self,
        execution_uuid: UUID,
        execution_info_queue: Queue[CommandExecutionInfo],
        intermediate_response_queue: Queue[IntermediateResponseType],
        logger: logging.Logger,
        lifetime_of_execution: Optional[timedelta],
    ):
        super().__init__(execution_uuid, execution_info_queue, logger, lifetime_of_execution)
        self.__intermediate_response_queue: Queue[IntermediateResponseType] = intermediate_response_queue

    def send_intermediate_response(self, value: IntermediateResponseType) -> None:
        """
        Send intermediate responses to subscribing clients

        Parameters
        ----------
        value
            The intermediate responses to send
        """
        self.__intermediate_response_queue.put(value)
