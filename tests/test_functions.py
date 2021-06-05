from typing import Iterable
from typing import Optional

import pytest

from jsonapy import BaseResource
from jsonapy import attributes_names
from jsonapy import fields_types
from jsonapy import relationships_names


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
        identifier_meta_attributes = {"gender"}


class ConcreteRelated(BaseResource):
    id: int
    important_concrete: ConcreteResource
    other_concretes: Iterable[ConcreteResource]


def test_attributes_names():
    assert attributes_names(ConcreteResource) == {"lastname", "optional", "name"}


def test_relationships_names():
    assert relationships_names(ConcreteRelated) == {"important_concrete", "other_concretes"}


def test_fields_types():
    assert fields_types(ConcreteRelated) == {"id": int,
                                             "important_concrete": ConcreteResource,
                                             "other_concretes": Iterable[ConcreteResource]}


def test_invalid_param():
    with pytest.raises(TypeError) as err:
        fields_types("abc")

    assert str(err.value) == f"'{str}' object is not a resource object."
