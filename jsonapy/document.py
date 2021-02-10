# Copyright (c) 2021 Guillaume Fayard
# This library is licensed under the MIT license
# For a complete copy of the license, see the LICENSE file.

""" # JSON:API document creation

> **WIP:** This module is under construction
"""

from typing import Dict
from typing import Iterable
from typing import Literal
from typing import Optional
from typing import Set
from typing import Union

from jsonapy import BaseResource


class JSONAPIDocument:
    def __init__(
        self,
        data: Union[BaseResource, Iterable[BaseResource]],
        required_attributes: Union[Iterable[str], Literal["__all__"]],
        relationships: Optional[Dict] = None,
        resource_links: Optional[Set[str]] = None,
        document_links: Optional[Dict] = None,
        included: Optional[Dict] = None
    ):
        # store data
        self.data = data

        # data-dumping-related attributes
        self.data_export_options = {
            "required_attributes": required_attributes,
            "relationships": relationships,
            "links": resource_links
        }

        # document-duming-related attributes
        self.links = document_links
        self.included = included

    def jsonapi_dict(self):
        try:
            data = [resource.jsonapi_dict(**self.data_export_options) for resource in self.data]
        except TypeError as err:
            if str(err) != f"'{type(self.data).__name__}' object is not iterable":
                raise
            data = self.data.jsonapi_dict(**self.data_export_options)
        return {"data": data}
