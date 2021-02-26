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


def test_optional_argument():
    inst = ConcreteResource(id=1, lastname="Hello", name="John")

    assert inst.optional == "Default"


def test_not_exported_attribute():
    """Initializing the object with more attributes should pass"""
    inst = ConcreteResource(id=1, name="John", lastname="Doe", gender="M")

    assert inst.gender == "M"
    assert inst._identifier_dict == {"type": "concrete", "id": 1, "meta": {"gender": "M"}}
    assert repr(inst) == "ConcreteResource(id=1, name='John', lastname='Doe', gender='M')"


def test_reserved_attribute():
    with pytest.raises(ValueError) as err:
        inst = ConcreteResource(id=1, name="John", lastname="Doe", jsonapi_dict="Illegal")

    assert str(err.value) == "\n    This attribute name is reserved: 'jsonapi_dict'."
