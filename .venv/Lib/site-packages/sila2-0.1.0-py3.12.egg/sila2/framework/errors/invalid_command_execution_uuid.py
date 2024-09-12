from sila2.framework.errors.framework_error import FrameworkError, FrameworkErrorType


class InvalidCommandExecutionUUID(FrameworkError):
    def __init__(self, message: str):
        super().__init__(FrameworkErrorType.INVALID_COMMAND_EXECUTION_UUID, message)
