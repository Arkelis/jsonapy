import pytest

from jsonapy.base import BaseResource


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


def test_resource_definition_with_relationship():
    class AResource(BaseResource):
        id: int

    class BResource(BaseResource):
        id: int
        rel: AResource

    assert BResource.__relationships_fields_set__ == {"rel"}
    assert BResource.__fields_types__ == {"id": int, "rel": AResource}


def test_resource_without_id():
    with pytest.raises(AttributeError) as err:

        class ResourceWithoutId(BaseResource):
            pass

    assert str(err.value) == "A Resource must have an 'id' attribute."


def test_abstract_resource():
    class AbstractResource(BaseResource):
        class Meta:
            is_abstract = True

    assert AbstractResource.__is_abstract__


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


def test_simple_link_registering():
    class AResource(BaseResource):
        id: int

    # define trivial function simulating URL factoring
    def link_factory(res_id):
        return str(res_id)

    AResource.register_link_factory("self", link_factory)

    assert AResource.__links_factories__ == {"self": link_factory}


def test_relationship_link_registering():
    class AResource(BaseResource):
        id: int

    class BResource(BaseResource):
        id: int
        rel: AResource

    def link_factory(res_id):
        return str(res_id)

    BResource.register_link_factory("rel__related", link_factory)

    assert BResource.__links_factories__ == {"rel__related": link_factory}


def test_invalid_relationship_link_registering():
    class AResource(BaseResource):
        id: int

    def link_factory(res_id):
        return str(res_id)

    with pytest.raises(ValueError) as err:
        AResource.register_link_factory("rel__related", link_factory)

    assert str(err.value) == "'rel' is not a valid relationship for AResource."