from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from sila2.framework import FullyQualifiedIdentifier
from sila2.server import FeatureImplementationBase

from .silaservice_types import GetFeatureDefinition_Responses, SetServerName_Responses


class SiLAServiceBase(FeatureImplementationBase, ABC):

    """

    This Feature MUST be implemented by each SiLA Server.

    It specifies Commands and Properties to discover the Features a SiLA Server implements as well as details
    about the SiLA Server, like name, type, description, vendor and UUID.

    Any interaction described in this feature MUST not affect the behaviour of any other Feature.

    """

    @abstractmethod
    def get_ServerName(self, *, metadata: Dict[FullyQualifiedIdentifier, Any]) -> str:
        """

        Human readable name of the SiLA Server. The name can be set using the 'Set Server Name' command.


          :param metadata: The SiLA Client Metadata attached to the call
          :return:
        Human readable name of the SiLA Server. The name can be set using the 'Set Server Name' command.

        """
        pass

    @abstractmethod
    def get_ServerType(self, *, metadata: Dict[FullyQualifiedIdentifier, Any]) -> str:
        """

        The type of this server. It, could be, e.g., in the case of a SiLA Device the model name.
        It is specified by the implementer of the SiLA Server and MAY not be unique.


          :param metadata: The SiLA Client Metadata attached to the call
          :return:
        The type of this server. It, could be, e.g., in the case of a SiLA Device the model name.
        It is specified by the implementer of the SiLA Server and MAY not be unique.

        """
        pass

    @abstractmethod
    def get_ServerUUID(self, *, metadata: Dict[FullyQualifiedIdentifier, Any]) -> str:
        """

        Globally unique identifier that identifies a SiLA Server. The Server UUID MUST be generated once
        and remain the same for all times.


          :param metadata: The SiLA Client Metadata attached to the call
          :return:
        Globally unique identifier that identifies a SiLA Server. The Server UUID MUST be generated once
        and remain the same for all times.

        """
        pass

    @abstractmethod
    def get_ServerDescription(self, *, metadata: Dict[FullyQualifiedIdentifier, Any]) -> str:
        """

        Description of the SiLA Server. This should include the use and purpose of this SiLA Server.


          :param metadata: The SiLA Client Metadata attached to the call
          :return:
        Description of the SiLA Server. This should include the use and purpose of this SiLA Server.

        """
        pass

    @abstractmethod
    def get_ServerVersion(self, *, metadata: Dict[FullyQualifiedIdentifier, Any]) -> str:
        """

        Returns the version of the SiLA Server. A "Major" and a "Minor" version number (e.g. 1.0) MUST be provided,
        a Patch version number MAY be provided. Optionally, an arbitrary text, separated by an underscore MAY be
        appended, e.g. “3.19.373_mighty_lab_devices”.


          :param metadata: The SiLA Client Metadata attached to the call
          :return:
        Returns the version of the SiLA Server. A "Major" and a "Minor" version number (e.g. 1.0) MUST be provided,
        a Patch version number MAY be provided. Optionally, an arbitrary text, separated by an underscore MAY be
        appended, e.g. “3.19.373_mighty_lab_devices”.

        """
        pass

    @abstractmethod
    def get_ServerVendorURL(self, *, metadata: Dict[FullyQualifiedIdentifier, Any]) -> str:
        """

        Returns the URL to the website of the vendor or the website of the product of this SiLA Server.
        This URL SHOULD be accessible at all times.
        The URL is a Uniform Resource Locator as defined in RFC 1738.


          :param metadata: The SiLA Client Metadata attached to the call
          :return:
        Returns the URL to the website of the vendor or the website of the product of this SiLA Server.
        This URL SHOULD be accessible at all times.
        The URL is a Uniform Resource Locator as defined in RFC 1738.

        """
        pass

    @abstractmethod
    def get_ImplementedFeatures(self, *, metadata: Dict[FullyQualifiedIdentifier, Any]) -> List[str]:
        """

        Returns a list of fully qualified Feature identifiers of all implemented Features of this SiLA Server.
        This list SHOULD remain the same throughout the lifetime of the SiLA Server.


          :param metadata: The SiLA Client Metadata attached to the call
          :return:
        Returns a list of fully qualified Feature identifiers of all implemented Features of this SiLA Server.
        This list SHOULD remain the same throughout the lifetime of the SiLA Server.

        """
        pass

    @abstractmethod
    def GetFeatureDefinition(
        self, FeatureIdentifier: str, *, metadata: Dict[FullyQualifiedIdentifier, Any]
    ) -> GetFeatureDefinition_Responses:
        """

        Get the Feature Definition of an implemented Feature by its fully qualified Feature Identifier.
        This command has no preconditions and no further dependencies and can be called at any time.



          :param FeatureIdentifier:
          The fully qualified Feature identifier for which the Feature definition shall be retrieved.


          :param metadata: The SiLA Client Metadata attached to the call
          :return:
              - FeatureDefinition: The Feature definition in XML format (according to the Feature Definition Schema).
        """
        pass

    @abstractmethod
    def SetServerName(
        self, ServerName: str, *, metadata: Dict[FullyQualifiedIdentifier, Any]
    ) -> SetServerName_Responses:
        """

        Sets a human readable name to the Server Name Property.Command has no preconditions and
        no further dependencies and can be called at any time.



          :param ServerName: The human readable name to assign to the SiLA Server.

          :param metadata: The SiLA Client Metadata attached to the call
          :return:

        """
        pass
