from __future__ import annotations

from typing import NamedTuple


class GetFeatureDefinition_Responses(NamedTuple):

    FeatureDefinition: str
    """
    The Feature definition in XML format (according to the Feature Definition Schema).
    """


class SetServerName_Responses(NamedTuple):

    pass
