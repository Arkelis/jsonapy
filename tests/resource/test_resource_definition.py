from typing import Generic
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple
from typing import TypeVar
from typing import Union

import pytest

from jsonapy.base import BaseResource


def make_link(x):
    return str(x)


def make_link2(x):
    return str(x)


def test_normal_resource_definition():
    class AResource(BaseResource):
        id: int
        name: str

    assert not AResource.__is_abstract__
    assert AResource.__resource_name__ == "AResource"
    assert AResource.__atomic_fields_set__ == {"name", "id"}
    assert AResource.__relationships_fields_set__ == set()
    assert AResource.__fields_types__ == {"id": int, "name": str}


def test_named_resource():
    class NamedResource(BaseResource):
        id: int

        class Meta:
            resource_name = "named"

    assert NamedResource.__resource_name__ == "named"


def test_resource_definition_with_relationships():
    class AResource(BaseResource):
        id: int

    class BResource(BaseResource):
        id: int
        rel: AResource
        opt_rel: Optional[AResource]
        it_rel: Iterable[AResource]
        opt_it_rel: Optional[Iterable[AResource]]

    assert BResource.__relationships_fields_set__ == {"rel", "opt_rel", "it_rel", "opt_it_rel"}
    assert BResource.__fields_types__ == {
        "id": int,
        "rel": AResource,
        "opt_rel": Optional[AResource],
        "it_rel": Iterable[AResource],
        "opt_it_rel": Optional[Iterable[AResource]],
    }


def test_resource_definition_with_complex_attributes():
    class AResource(BaseResource):
        id: int
        optional: Optional[str]
        union_of_three: Union[str, int, Tuple[str, int]]
        union_of_two: Union[str, int]
        iterable: Iterable[str]
        optional_iterable: Optional[Iterable[str]]
        list: List[int]

    assert AResource.__relationships_fields_set__ == set()
    assert AResource.__atomic_fields_set__ == {
        "id", "union_of_two", "union_of_three", "optional", "iterable", "optional_iterable", "list"}
    assert AResource.__fields_types__ == {
        "id": int,
        "optional": Optional[str],
        "union_of_three": Union[str, int, Tuple[str, int]],
        "union_of_two": Union[str, int],
        "iterable": Iterable[str],
        "optional_iterable": Optional[Iterable[str]],
        "list": List[int],
    }


def test_resource_without_id():
    with pytest.raises(AttributeError) as err:

        class ResourceWithoutId(BaseResource):
            pass

    assert str(err.value) == "A Resource must have an 'id' attribute."


def test_resource_with_meta_attributes():
    class AbstractResource(BaseResource):
        class Meta:
            is_abstract = True
            identifier_meta_fields = ["a", "b"]

    assert AbstractResource.__is_abstract__
    assert AbstractResource.__identifier_meta_fields__ == {"a", "b"}


def test_concrete_inheriting_from_abstract():
    class AbstRes(BaseResource):
        name: str

        class Meta:
            is_abstract = True

    class ConcreteRes(AbstRes):
        id: int

    assert not ConcreteRes.__is_abstract__
    assert ConcreteRes.__fields_types__ == {"id": int, "name": str}
    assert ConcreteRes.__atomic_fields_set__ == {"name", "id"}
    assert ConcreteRes.__relationships_fields_set__ == set()


def test_linked_resource():
    class AResource(BaseResource):
        id: int

        class Meta:
            links_factories = {"self": make_link}

    AResource.register_link_factory("other_link", make_link2)

    assert AResource.__links_factories__ == {"self": make_link, "other_link": make_link2}


def test_relationship_link():
    class AResource(BaseResource):
        id: int

    class BResource(BaseResource):
        id: int
        rel: AResource

        class Meta:
            links_factories = {"rel__related": make_link}

    BResource.register_link_factory("rel__self", make_link2)

    assert BResource.__links_factories__ == {"rel__related": make_link, "rel__self": make_link2}


def test_invalid_relationship_link():
    with pytest.raises(ValueError) as err:
        class AResource(BaseResource):
            id: int

            class Meta:
                links_factories = {"rel__related": make_link}

    assert str(err.value) == "'rel' is not a valid relationship for AResource."


def test_invalid_relationship_link_registering():
    class AResource(BaseResource):
        id: int

    with pytest.raises(ValueError) as err:
        AResource.register_link_factory("rel__related", make_link)

    assert str(err.value) == "'rel' is not a valid relationship for AResource."
