import pytest

from jsonapy.base import BaseResource


class AbstractResource(BaseResource):
    name: str

    class Meta:
        is_abstract = True


class ConcreteResource(AbstractResource):
    lastname: str
    id: int

    class Meta:
        resource_name = "concrete"
        identifier_meta_fields = {"gender"}


def test_concrete_instantiation():
    inst = ConcreteResource(id=1, name="John", lastname="Doe")

    assert inst.id == 1


def test_missing_argument():
    with pytest.raises(ValueError) as err:
        inst = ConcreteResource(id=1, name="John")

    assert str(err.value) == "\n    Missing argument: 'lastname'."


def test_not_exported_attribute():
    """Initializing the object with more attributes should pass"""
    inst = ConcreteResource(id=1, name="John", lastname="Doe", gender="M")

    assert inst.gender == "M"
    assert inst._identifier_dict == {"type": "concrete", "id": 1, "meta": {"gender": "M"}}


def test_reserved_attribute():
    with pytest.raises(ValueError) as err:
        inst = ConcreteResource(id=1, name="John", lastname="Doe", jsonapi_dict="Illegal")

    assert str(err.value) == "\n    This attribute name is reserved: 'jsonapi_dict'."
