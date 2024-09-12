from __future__ import annotations

import logging
from collections import defaultdict
from queue import Queue
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterator, Optional
from uuid import UUID

from google.protobuf.message import Message
from grpc import ServicerContext

from sila2.framework.command.execution_info import CommandExecutionInfo
from sila2.framework.errors.invalid_command_execution_uuid import InvalidCommandExecutionUUID
from sila2.framework.feature import Feature
from sila2.framework.fully_qualified_identifier import FullyQualifiedIdentifier
from sila2.framework.utils import raise_as_rpc_error
from sila2.server.feature_implementation_base import FeatureImplementationBase
from sila2.server.observables.observable_command_manager import ObservableCommandManager
from sila2.server.observables.subscription_manager_thread import SubscriptionManagerThread
from sila2.server.utils import (
    _find_allowed_defined_execution_errors,
    extract_metadata,
    raises_rpc_errors,
    unpack_parameters,
)

if TYPE_CHECKING:
    from sila2.pb2_stubs.SiLAFramework_pb2 import CommandExecutionUUID as SilaCommandExecutionUUID
    from sila2.server.sila_server import SilaServer

logger = logging.getLogger(__name__)


class FeatureImplementationServicer:
    parent_server: SilaServer
    feature: Feature
    implementation: Optional[FeatureImplementationBase]
    observable_command_managers: Dict[str, Dict[UUID, ObservableCommandManager]]
    observable_property_subscription_managers: Dict[str, SubscriptionManagerThread]

    def __init__(self, parent_server: SilaServer, feature: Feature):
        self.parent_server = parent_server
        self.feature = feature
        self.implementation = None
        self.observable_command_managers = defaultdict(dict)
        self.observable_property_subscription_managers = {}

    def _set_implementation(self, implementation: FeatureImplementationBase):
        self.implementation = implementation
        self.__start_observable_property_listeners()

        for prop in self.feature._unobservable_properties.values():
            setattr(self, f"Get_{prop._identifier}", self.__get_unobservable_property_get_call(prop._identifier))
        for cmd in self.feature._unobservable_commands.values():
            setattr(self, cmd._identifier, self.__get_unobservable_command_init_call(cmd._identifier))
        for prop in self.feature._observable_properties.values():
            setattr(
                self, f"Subscribe_{prop._identifier}", self.__get_observable_property_subscribe_call(prop._identifier)
            )
        for cmd in self.feature._observable_commands.values():
            setattr(self, cmd._identifier, self.__get_observable_command_init_call(cmd._identifier))
            setattr(self, f"{cmd._identifier}_Info", self.__get_observable_command_info_subscribe_call(cmd._identifier))
            setattr(
                self,
                f"{cmd._identifier}_Intermediate",
                self.__get_observable_command_intermediate_subscribe_call(cmd._identifier),
            )
            setattr(self, f"{cmd._identifier}_Result", self.__get_observable_command_result_get_call(cmd._identifier))
        for metadata in self.feature.metadata_definitions.values():
            setattr(
                self,
                f"Get_FCPAffectedByMetadata_{metadata._identifier}",
                self.__get_fpc_affected_by_metadata_call(metadata._identifier),
            )

    def __start_observable_property_listeners(self):
        for prop in self.feature._observable_properties.values():
            manager = SubscriptionManagerThread(
                prop.fully_qualified_identifier,
                getattr(self.implementation, f"_{prop._identifier}_producer_queue"),
                prop.to_message,
            )
            self.observable_property_subscription_managers[prop._identifier] = manager
            manager.start()

    def __get_observable_command_manager(
        self, command_id: str, execution_uuid: UUID, context: ServicerContext
    ) -> ObservableCommandManager:
        manager = self.observable_command_managers[command_id].get(execution_uuid)
        if manager is None:
            error = InvalidCommandExecutionUUID(
                f"There is no instance of Countdown with the execution uuid {execution_uuid}"
            )
            raise_as_rpc_error(error, context)
        return manager

    def __get_unobservable_command_init_call(self, command_id: str) -> Callable[[Message, ServicerContext], Message]:
        cmd = self.feature._unobservable_commands[command_id]
        impl_func: Callable = getattr(self.implementation, command_id)

        def wrapper(request: Message, context: ServicerContext) -> Message:
            metadata = extract_metadata(context, self.parent_server, cmd)
            allowed_errors = _find_allowed_defined_execution_errors(self.parent_server, cmd, metadata.keys())

            with raises_rpc_errors(context, allowed_errors):
                params = cmd.parameters.to_native_type(request)
                self.__apply_metadata_interceptors(None, metadata, cmd.fully_qualified_identifier)
                response = impl_func(*params, metadata=metadata)
                return cmd.responses.to_message(response)

        return wrapper

    def __get_unobservable_property_get_call(self, property_id: str) -> Callable[[Message, ServicerContext], Message]:
        prop = self.feature._unobservable_properties[property_id]
        impl_func: Callable = getattr(self.implementation, f"get_{property_id}")

        def wrapper(request, context: ServicerContext):
            metadata = extract_metadata(context, self.parent_server, prop)
            allowed_errors = _find_allowed_defined_execution_errors(self.parent_server, prop, metadata.keys())

            with raises_rpc_errors(context, allowed_errors):
                self.__apply_metadata_interceptors(None, metadata, prop.fully_qualified_identifier)
                response = impl_func(metadata=metadata)
                return prop.to_message(response)

        return wrapper

    def __get_observable_command_init_call(self, command_id: str) -> Callable[[Message, ServicerContext], Message]:
        cmd = self.feature._observable_commands[command_id]
        impl_func: Callable = getattr(self.implementation, command_id)

        def wrapper(request: Message, context: ServicerContext) -> Message:
            metadata = extract_metadata(context, self.parent_server, cmd)
            allowed_errors = _find_allowed_defined_execution_errors(self.parent_server, cmd, metadata.keys())

            params = unpack_parameters(cmd, request, context)

            if cmd.intermediate_responses is None:

                def _func_to_execute(execution_info_queue: Queue[CommandExecutionInfo]) -> Message:
                    with raises_rpc_errors(context, allowed_errors):
                        self.__apply_metadata_interceptors(None, metadata, cmd.fully_qualified_identifier)
                        response = impl_func(
                            *params,
                            metadata=metadata,
                            execution_info_queue=execution_info_queue,
                        )
                        return cmd.responses.to_message(response)

            else:

                def _func_to_execute(
                    intermediate_response_queue: Queue[Any], execution_info_queue: Queue[CommandExecutionInfo]
                ) -> Message:
                    with raises_rpc_errors(context, allowed_errors):
                        self.__apply_metadata_interceptors(None, metadata, cmd.fully_qualified_identifier)
                        response = impl_func(
                            *params,
                            metadata=metadata,
                            intermediate_response_queue=intermediate_response_queue,
                            execution_info_queue=execution_info_queue,
                        )
                        return cmd.responses.to_message(response)

            command_manager = ObservableCommandManager(self.parent_server, cmd, _func_to_execute, metadata.keys())
            self.observable_command_managers[command_id][command_manager.command_execution_uuid] = command_manager

            return self.feature._pb2_module.SiLAFramework__pb2.CommandConfirmation(
                commandExecutionUUID=self.feature._pb2_module.SiLAFramework__pb2.CommandExecutionUUID(
                    value=str(command_manager.command_execution_uuid)
                )
            )

        return wrapper

    def __get_observable_command_info_subscribe_call(
        self, command_id: str
    ) -> Callable[[SilaCommandExecutionUUID, ServicerContext], Iterator[Message]]:
        def wrapper(request: SilaCommandExecutionUUID, context: ServicerContext) -> Iterator[Message]:
            manager = self.__get_observable_command_manager(command_id, UUID(request.value), context)

            with raises_rpc_errors(context):
                for value in manager.subscribe_to_execution_infos():
                    yield value

        return wrapper

    def __get_observable_command_intermediate_subscribe_call(
        self, command_id: str
    ) -> Callable[[SilaCommandExecutionUUID, ServicerContext], Iterator[Message]]:
        def wrapper(request: SilaCommandExecutionUUID, context: ServicerContext) -> Iterator[Message]:
            manager = self.__get_observable_command_manager(command_id, UUID(request.value), context)

            with raises_rpc_errors(context):
                for value in manager.subscribe_to_intermediate_responses():
                    yield value

        return wrapper

    def __get_observable_command_result_get_call(
        self, command_id: str
    ) -> Callable[[SilaCommandExecutionUUID, ServicerContext], Message]:
        cmd = self.feature._observable_commands[command_id]

        def wrapper(request: SilaCommandExecutionUUID, context: ServicerContext) -> Message:
            manager = self.__get_observable_command_manager(command_id, UUID(request.value), context)
            allowed_errors = _find_allowed_defined_execution_errors(
                self.parent_server, cmd, manager.metadata_identifiers
            )

            with raises_rpc_errors(context, allowed_errors):
                return manager.get_responses()

        return wrapper

    def __get_observable_property_subscribe_call(
        self, property_id: str
    ) -> Callable[[Message, ServicerContext], Iterator[Message]]:
        prop = self.feature._observable_properties[property_id]
        manager = self.observable_property_subscription_managers[property_id]
        impl_func = getattr(self.implementation, f"{property_id}_on_subscription", None)

        def wrapper(request: Message, context: ServicerContext) -> Iterator[Message]:
            metadata = extract_metadata(context, self.parent_server, prop)
            allowed_errors = _find_allowed_defined_execution_errors(self.parent_server, prop, metadata.keys())

            with raises_rpc_errors(context, allowed_errors):
                self.__apply_metadata_interceptors(None, metadata, prop.fully_qualified_identifier)

                if impl_func is not None:
                    impl_func(metadata=metadata)

                for value in manager.add_subscription():
                    yield value

        return wrapper

    def __get_fpc_affected_by_metadata_call(self, metadata_id: str) -> Callable[[Message, ServicerContext], Message]:
        metadata_node = self.feature.metadata_definitions[metadata_id]
        impl_func = getattr(self.implementation, f"get_calls_affected_by_{metadata_id}")

        def wrapper(request: Message, context: ServicerContext) -> Message:
            with raises_rpc_errors(context):
                return metadata_node.to_affected_calls_message(impl_func())

        return wrapper

    def cancel_all_subscriptions(self):
        for manager in self.observable_property_subscription_managers.values():
            manager.cancel_producer()

    def __apply_metadata_interceptors(
        self, parameters: Any, metadata: Dict[FullyQualifiedIdentifier, Any], target: FullyQualifiedIdentifier
    ):
        for interceptor in self.parent_server.metadata_interceptors:
            interceptor.intercept(parameters, metadata, target)
