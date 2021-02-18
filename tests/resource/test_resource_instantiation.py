from typing import Any
from typing import Dict
from typing import Iterable
from typing import Optional
from typing import Union

import pytest

from jsonapy.base import BaseResource


class AbstractResource(BaseResource):
    name: str

    class Meta:
        is_abstract = True


class ConcreteResource(AbstractResource):
    lastname: str
    id: int
    optional: Optional[str] = "Default"

    class Meta:
        resource_name = "concrete"
        identifier_meta_fields = {"gender"}


class ConcreteRelated(BaseResource):
    id: int
    important_concrete: ConcreteResource
    other_concretes: Iterable[ConcreteResource]


class ResourceWithComplexAttribute(BaseResource):
    id: int
    complex_attr: Union[int, str, bool]
    union_without_none: Union[int, str]
    other: Dict[Any, Any]


def test_concrete_instantiation():
    inst = ConcreteResource(id=1, name="John", lastname="Doe", optional="Hello")

    assert inst.id == 1
    assert inst.optional == "Hello"


def test_instance_with_relations():
    important_related = ConcreteResource(id=1, name="Guido", lastname="Van Rossum")
    others = [
        ConcreteResource(id=2, name="Fred", lastname="Drake"),
        ConcreteResource(id=3, name="Georg", lastname="Brandl")
    ]
    inst = ConcreteRelated(id=1, important_concrete=important_related, other_concretes=others)

    assert inst.important_concrete == important_related
    assert inst.other_concretes == others


def test_missing_argument():
    # simple check
    with pytest.raises(ValueError) as err1:
        inst = ConcreteResource(id=1, optional="Hello", name="John")

    # this covers utils.is_an_optional_field
    with pytest.raises(ValueError) as err2:
        inst = ResourceWithComplexAttribute()

    assert str(err1.value) == "\n    Missing argument: 'lastname'."
    assert (
        "\n    Missing argument: 'other'." in str(err2.value)
        and "\n    Missing argument: 'complex_attr'." in str(err2.value)
        and "\n    Missing argument: 'union_without_none'." in str(err2.value)
        and "\n    Missing argument: 'id'." in str(err2.value)
    )


def test_optional_argument():
    inst = ConcreteResource(id=1, lastname="Hello", name="John")

    assert inst.optional == "Default"


def test_not_exported_attribute():
    """Initializing the object with more attributes should pass"""
    inst = ConcreteResource(id=1, name="John", lastname="Doe", gender="M")

    assert inst.gender == "M"
    assert inst._identifier_dict == {"type": "concrete", "id": 1, "meta": {"gender": "M"}}


def test_reserved_attribute():
    with pytest.raises(ValueError) as err:
        inst = ConcreteResource(id=1, name="John", lastname="Doe", jsonapi_dict="Illegal")

    assert str(err.value) == "\n    This attribute name is reserved: 'jsonapi_dict'."
