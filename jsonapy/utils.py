# Copyright (c) 2021 Guillaume Fayard
# This library is licensed under the MIT license
# For a complete copy of the license, see the LICENSE file.


def snake_to_camel_case(text: str) -> str:
    """Convert a snake_case string into camelCase format.
    This function doesnt check that passed text is in snake case.
    """
    first, *others = text.split("_")
    return first + "".join(map(str.capitalize, others))
