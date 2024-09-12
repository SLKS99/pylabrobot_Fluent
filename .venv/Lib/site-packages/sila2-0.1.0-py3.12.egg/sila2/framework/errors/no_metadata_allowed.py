from sila2.framework.errors.framework_error import FrameworkError, FrameworkErrorType


class NoMetadataAllowed(FrameworkError):
    def __init__(self, message: str):
        super().__init__(FrameworkErrorType.NO_METADATA_ALLOWED, message)
