# Copyright (c) 2021 Guillaume Fayard
# This library is licensed under the MIT license
# For a complete copy of the license, see the LICENSE file.

""" # Utilitarian functions

This module defines utilitarian members used in the library.
"""
import collections.abc
import functools
import re
import typing
from typing import Union


def snake_to_camel_case(text: str, dontformat: bool = False) -> str:
    """Convert a snake_case string into camelCase format if needed.

    This function doesnt check that passed text is in snake_case.
    If dontformat is True, return text.
    """
    if dontformat:
        return text
    first, *others = text.split("_")
    return first + "".join(map(str.capitalize, others))


def camel_to_snake_case(text: str) -> str:
    """Convert a camelCase string into snake_case format.

    This function does not check that passed text is in camelCase.
    See https://stackoverflow.com/a/12867228/9214306

    This version handles simple cases as there is no known complicated case in
    the application (in the defined models).
    """
    return re.sub(r"([A-Z]+)", r"_\1", text).lower()


def is_type_hint_instance_of(type_hint, mcs) -> bool:
    """Check if `type_hint` contains a `mcs` instance.

    This is an utilitarian function for `BaseResourceMeta`.

    ###### Parameters ######

    * `type_hint`: type hint to check
    * `mcs`: metaclass to check

    For a given class `C`, instance of metaclass `MC`, all following expressions
    are evaluated to `True`:

    ```python
    is_type_hint_instance_of(C, MC)
    is_type_hint_instance_of(Iterable[C], MC)
    is_type_hint_instance_of(Optional[C], MC)
    is_type_hint_instance_of(Union[C, None], MC)
    is_type_hint_instance_of(Optional[Iterable[C]], MC)
    is_type_hint_instance_of(Union[Iterable[C], None], MC)
    ```

    ###### Returned value ######

    `True` in the shown cases, `Fasle` otherwise.
    """
    if isinstance(type_hint, mcs):
        return True
    origin = typing.get_origin(type_hint)
    if origin is None:
        return False
    type_args = typing.get_args(type_hint)
    if origin is Union:
        # in case of Optional field, check if it is Union[BaseResourceMeta, None]
        if len(type_args) != 2:
            return False
        if type(None) not in type_args:
            return False
        return is_type_hint_instance_of(type_args[0], mcs)
    if origin is collections.abc.Iterable:
        # in case of an iterable, check if it is a BaseResource
        return is_type_hint_instance_of(type_args[0], mcs)
    return False


def is_an_iterable_type_hint(rel_type_hint) -> bool:
    """Check if typing.Iterable wraps the relationship type hint.

    ###### Parameters ######

    * `rel_type_hint`: type hint to check

    For a given class `C`, all following expressions are evaluated to `True`:

    ```python
    is_an_iterable_type_hint(Iterable[C])
    is_an_iterable_type_hint(Optional[Iterable[C]])
    ```

    This does not check that the passed hint concerns a valid resource (see
    `is_type_hint_instance_of()`).

    ###### Returned value ######

    `True` in the shown cases, `Fasle` otherwise.
    """
    return (collections.abc.Iterable is typing.get_origin(rel_type_hint)
            or (collections.abc.Iterable
                in (typing.get_origin(tp) for tp in typing.get_args(rel_type_hint))))


@functools.lru_cache
def is_an_optional_type_hint(type_hint) -> bool:
    """Check if typing.Optional wraps the type hint.

    This is an utilitarian function for `jsonapy.base.BaseResource.__init__`.

    ###### Parameters ######

    * `type_hint`: type hint to check

    For a given class `C`, the following expressions is evaluated to `True`:

    ```python
    is_an_optional_type_hint(Optional[C])
    ```

    ###### Returned value ######

    `True` in the shown case, `Fasle` otherwise.
    """
    origin = typing.get_origin(type_hint)
    if origin is None:
        return False
    type_args = typing.get_args(type_hint)
    if origin is Union:
        # in case of Optional field, check if it is Union[..., None]
        if len(type_args) != 2:
            return False
        if type(None) not in type_args:
            return False
        return True
    return False

