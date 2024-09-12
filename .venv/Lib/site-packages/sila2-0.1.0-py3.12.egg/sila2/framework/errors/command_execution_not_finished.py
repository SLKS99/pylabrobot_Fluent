from sila2.framework.errors.framework_error import FrameworkError, FrameworkErrorType


class CommandExecutionNotFinished(FrameworkError):
    def __init__(self, message: str):
        super().__init__(FrameworkErrorType.COMMAND_EXECUTION_NOT_FINISHED, message)
