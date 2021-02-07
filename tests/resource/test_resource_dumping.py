import json
from typing import Callable

import pytest

from jsonapy import BaseResource


class SimpleResource(BaseResource):
    id: int
    name: str

    class Meta:
        resource_name = "less"


class MoreAttributes(SimpleResource):
    last_name: str
    birth_date: int

    class Meta:
        resource_name = "more"


class RelatedResource(BaseResource):
    related_more: MoreAttributes
    id: int
    foo: str

    class Meta:
        resource_name = "related"


def link_factory(res_name) -> Callable[[str], str]:
    def make_link(res_id) -> str:
        return f"http://example.com/{res_name}/{res_id}"
    return make_link


def rel_link_factory(res_name, rel_name) -> Callable[[str, str], str]:
    def make_link(res_id) -> str:
        return f"http://example.com/{res_name}/{res_id}/{rel_name}"
    return make_link


SimpleResource.register_link_factory("self", link_factory(SimpleResource.__resource_name__))
MoreAttributes.register_link_factory("self", link_factory(MoreAttributes.__resource_name__))
RelatedResource.register_link_factory("self", link_factory(RelatedResource.__resource_name__))
RelatedResource.register_link_factory("related_more__related", rel_link_factory(RelatedResource.__resource_name__, "related_more"))


@pytest.fixture
def simple_object() -> SimpleResource:
    return SimpleResource(id=0, name="Simple Name")


@pytest.fixture
def more_object() -> SimpleResource:
    return MoreAttributes(id=1, last_name="Last", name="Name", birth_date=1991)


@pytest.fixture
def related_object(more_object: MoreAttributes) -> RelatedResource:
    return RelatedResource(related_more=more_object, id=2, foo="bar")


def test_simple_dumping(simple_object: SimpleResource):
    expected = {
        "type": "less",
        "id": 0,
        "attributes": {"name": "Simple Name"},
    }
    assert (
        simple_object.jsonapi_dict(
            required_attributes="__all__",
        )
        == expected
    )


def test_simple_dumping_with_link(simple_object: SimpleResource):
    expected = {
        "type": "less",
        "id": 0,
        "attributes": {"name": "Simple Name"},
        "links": {"self": "http://example.com/less/0"},
    }
    assert (
        simple_object.jsonapi_dict(
            required_attributes="__all__",
            links={"self"},
        )
    ) == expected


def test_simple_dumping_with_filtered_attrs(more_object: MoreAttributes):
    expected = {
        "type": "more",
        "id": 1,
        "attributes": {"birthDate": 1991},
    }
    assert more_object.jsonapi_dict(required_attributes=["birth_date"]) == expected


def test_relationship_with_identifier_only(related_object: RelatedResource):
    expected = {
        "type": "related",
        "id": 2,
        "attributes": {"foo": "bar"},
        "relationships": {
            "related_more": {
                "data": {"type": "more", "id": 1}
            }
        }
    }
    assert (
        related_object.jsonapi_dict(
            required_attributes="__all__",
            relationships={"related_more": {"data": True}}
        )
        == expected
    )


def test_relationship_with_link_only(related_object: RelatedResource):
    expected = {
        "type": "related",
        "id": 2,
        "attributes": {"foo": "bar"},
        "relationships": {
            "related_more": {
                "links": {"related": "http://example.com/related/2/related_more"}
            }
        }
    }

    assert (
        related_object.jsonapi_dict(
            required_attributes="__all__",
            relationships={"related_more": {"data": False, "links": {"related"}}}
        )
        == related_object.jsonapi_dict(
            required_attributes="__all__",
            relationships={"related_more": {"links": {"related"}}}
        )
        == expected
    )


def test_relationship_with_nothing(related_object: RelatedResource):
    with pytest.raises(ValueError) as err:
        related_object.jsonapi_dict(
            required_attributes="__all__",
            relationships={"related_more": {"foo": "bar"}}
        )

    assert str(err.value) == "\n    You must provide at least links or data for the 'related_more' relationship."


def test_relationship_with_data_and_link(related_object: RelatedResource):
    expected = {
        "type": "related",
        "id": 2,
        "attributes": {"foo": "bar"},
        "relationships": {
            "related_more": {
                "data": {"type": "more", "id": 1},
                "links": {"related": "http://example.com/related/2/related_more"}
            }
        }
    }
    assert (
        related_object.jsonapi_dict(
            required_attributes="__all__",
            relationships={"related_more": {"data": True, "links": {"related"}}}
        )
        == expected
    )


def test_str_dump(related_object: RelatedResource):
    expected = json.dumps({
        "type": "related",
        "id": 2,
        "attributes": {"foo": "bar"},
        "relationships": {
            "related_more": {
                "data": {"type": "more", "id": 1},
                "links": {"related": "http://example.com/related/2/related_more"}
            }
        }
    })
    assert (
        related_object.dump(
            required_attributes="__all__",
            relationships={"related_more": {"data": True, "links": {"related"}}}
        )
        == expected
    )
