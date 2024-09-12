from __future__ import annotations

from typing import TYPE_CHECKING, Callable, List

from sila2.features.silaservice import SiLAServiceBase, UnimplementedFeature
from sila2.framework.errors.no_metadata_allowed import NoMetadataAllowed

if TYPE_CHECKING:
    from sila2.server.sila_server import SilaServer


def no_metadata_allowed(func: Callable):
    def wrapper(*args, **kwargs):
        metadata = kwargs.pop("metadata")
        if metadata:
            raise NoMetadataAllowed(f"SiLAService.{func.__name__} received metadata {list(metadata.keys())}")
        return func(*args, **kwargs)

    return wrapper


class SiLAServiceImpl(SiLAServiceBase):
    parent_server: SilaServer

    def __init__(self, parent_server: SilaServer):
        self.parent_server = parent_server

    @no_metadata_allowed
    def GetFeatureDefinition(self, FeatureIdentifier: str) -> str:
        if FeatureIdentifier not in (f.fully_qualified_identifier for f in self.parent_server.features.values()):
            raise UnimplementedFeature(f"Feature {FeatureIdentifier} is not implemented by this server")

        return self.parent_server.features[FeatureIdentifier.split("/")[-2]]._feature_definition

    @no_metadata_allowed
    def SetServerName(self, ServerName: str) -> None:
        self.parent_server.server_name = ServerName

    @no_metadata_allowed
    def get_ImplementedFeatures(self) -> List[str]:
        return [f.fully_qualified_identifier for f in self.parent_server.features.values()]

    @no_metadata_allowed
    def get_ServerName(self) -> str:
        return self.parent_server.server_name

    @no_metadata_allowed
    def get_ServerType(self) -> str:
        return self.parent_server.server_type

    @no_metadata_allowed
    def get_ServerUUID(self) -> str:
        return str(self.parent_server.server_uuid)

    @no_metadata_allowed
    def get_ServerDescription(self) -> str:
        return self.parent_server.server_description

    @no_metadata_allowed
    def get_ServerVersion(self) -> str:
        return self.parent_server.server_version

    @no_metadata_allowed
    def get_ServerVendorURL(self) -> str:
        return self.parent_server.server_vendor_url
