# Copyright (c) 2021 Guillaume Fayard
# This library is licensed under the MIT license
# For a complete copy of the license, see the LICENSE file.

"""# Top level functions

This module provides functions for accessing special attributes in a public way.
"""
import functools
from typing import Any
from typing import Dict
from typing import Set
from typing import Type
from typing import Union

from jsonapy.base import BaseResource
from jsonapy.base import BaseResourceMeta


def _check_resource_type(func):
    @functools.wraps(func)
    def wrapper(resource_instance_or_class: Union[Type[BaseResource], BaseResource]):
        if (
            not isinstance(resource_instance_or_class, BaseResource)
            and not isinstance(resource_instance_or_class, BaseResourceMeta)
        ):
            raise TypeError(f"'{resource_instance_or_class.__class__}' object is not a resource object.")
        return func(resource_instance_or_class)
    return wrapper


@_check_resource_type
def fields_types(resource_instance_or_class: Union[Type[BaseResource], BaseResource]) -> Dict[str, Any]:
    """Return a dictionary of the fields types of the resource.

    ###### Returned value ######

    This functions actually returns `resource_instance_or_class.__fields_types__`.
    (See `jsonapy.base.BaseResourceMeta`.)

    ###### Errors raised ######

    `resource_instance_or_class` must be a `BaseResource` instance or subclass,
    otherwise a `TypeError` is raised.
    """
    return resource_instance_or_class.__fields_types__


@_check_resource_type
def relationships_names(resource_instance_or_class: Union[Type[BaseResource], BaseResource]) -> Set[str]:
    """Return a set containing the relationships names of the resource.

    ###### Returned value ######

    This functions actually returns `resource_instance_or_class.__relationships_fields_set__`.
    (See `jsonapy.base.BaseResourceMeta`.)

    ###### Errors raised ######

    `resource_instance_or_class` must be a `BaseResource` instance or subclass,
    otherwise a `TypeError` is raised.
    """
    return resource_instance_or_class.__relationships_fields_set__


@_check_resource_type
def attributes_names(resource_instance_or_class: Union[Type[BaseResource], BaseResource]) -> Set[str]:
    """Return a set containing the attributes names of the resource.

    ###### Returned value ######

    This functions actually returns `resource_instance_or_class.__atomic_fields_set__ - {"id"}`.
    (See `jsonapy.base.BaseResourceMeta`.)

    ###### Errors raised ######

    `resource_instance_or_class` must be a `BaseResource` instance or subclass,
    otherwise a `TypeError` is raised.
    """
    return resource_instance_or_class.__atomic_fields_set__ - {"id"}
