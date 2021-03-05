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

from jsonapy import BaseResource


def _check_resource_type(func):
    @functools.wraps(func)
    def wrapper(resource_instance: BaseResource):
        if not isinstance(resource_instance, BaseResource):
            raise TypeError(f"'{resource_instance.__class__.__name__}' object is not a resource object.")
        return func(resource_instance)
    return wrapper


@_check_resource_type
def fields_types(resource_instance: BaseResource) -> Dict[str, Any]:
    """Return `resource_instance.__fields_types__`

    `resource_instance` must be a `BaseResource` instance, otherwise a
    `TypeError` is raised.
    """
    return resource_instance.__fields_types__


@_check_resource_type
def relationships_names(resource_instance: BaseResource) -> Set[str]:
    """Return `resource_instance.__relationships_fields_set__`

    `resource_instance` must be a `BaseResource` instance, otherwise a
    `TypeError` is raised.
    """
    return resource_instance.__relationships_fields_set__


@_check_resource_type
def attributes_names(resource_instance: BaseResource) -> Set[str]:
    """Return `resource_instance.__atomic_fields_set__ - {"id"}`

    `resource_instance` must be a `BaseResource` instance, otherwise a
    `TypeError` is raised.
    """
    return resource_instance.__atomic_fields_set__ - {"id"}
