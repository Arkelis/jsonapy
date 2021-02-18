# Copyright (c) 2021 Guillaume Fayard
# This library is licensed under the MIT license
# For a complete copy of the license, see the LICENSE file.

""" # JSON:API document creation

> **WIP:** This module is under construction
"""
import collections.abc
from typing import Dict
from typing import Iterable
from typing import Literal
from typing import Optional
from typing import Set
from typing import Union

from jsonapy import BaseResource
from jsonapy import base


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
        if isinstance(data, collections.abc.Iterable):
            if all(isinstance(obj, BaseResource) for obj in data):
                self.single = False
            else:
                raise TypeError("Data must be resource objets.")
        elif isinstance(data, base.BaseResource):
            self.single = True
        else:
            raise ValueError("Data must be a resource object.")
        self.data: Union[Iterable[BaseResource], BaseResource] = data


        # data-dumping-related attributes
        self.data_export_options = {
            "required_attributes": required_attributes,
            "relationships": relationships,
            "links": resource_links
        }

        # document-duming-related attributes
        # links
        self.links = document_links
        
        # related objects inclusion
        self._validate_inclusion(included)
        self.included = included

    def jsonapi_dict(self):
        data = (
            [obj.jsonapi_dict(**self.data_export_options) for obj in self.data]
            if not self.single
            else self.data.jsonapi_dict(**self.data_export_options)
        )
        return {"data": data}

    def _validate_inclusion(self, included):
        ...
