import json

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
        "links": {"self": "http://example.com/simple/0"},
    }
    assert (
        simple_object.jsonapi_dict(
            required_attributes="__all__",
            links={"self": "http://example.com/simple/0"},
        )
        == expected
    )


def test_simple_dumping_without_link(simple_object: SimpleResource):
    expected = {
        "type": "less",
        "id": 0,
        "attributes": {"name": "Simple Name"},
    }
    assert simple_object.jsonapi_dict(required_attributes="__all__") == expected


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
                "links": {"self": "http://example.com/rel/2/more"}
            }
        }
    }
    assert (
        related_object.jsonapi_dict(
            required_attributes="__all__",
            relationships={"related_more": {"data": False, "links": {"self": "http://example.com/rel/2/more"}}}
        )
        == related_object.jsonapi_dict(
            required_attributes="__all__",
            relationships={"related_more": {"links": {"self": "http://example.com/rel/2/more"}}}
        )
        == expected
    )


def test_relationship_with_nothing(related_object: RelatedResource):
    with pytest.raises(ValueError) as err:
        related_object.jsonapi_dict(
            required_attributes="__all__",
            relationships={"related_more": {"foo": "bar"}}
        )

    assert str(err.value) == f"You must provide at least links or data for the 'related_more' relationship."


def test_relationship_with_data_and_link(related_object: RelatedResource):
    expected = {
        "type": "related",
        "id": 2,
        "attributes": {"foo": "bar"},
        "relationships": {
            "related_more": {
                "data": {"type": "more", "id": 1},
                "links": {"self": "http://example.com/rel/2/more"}
            }
        }
    }
    assert (
        related_object.jsonapi_dict(
            required_attributes="__all__",
            relationships={"related_more": {"data": True, "links": {"self": "http://example.com/rel/2/more"}}}
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
                "links": {"self": "http://example.com/rel/2/more"}
            }
        }
    })
    assert (
        related_object.dump(
            required_attributes="__all__",
            relationships={"related_more": {"data": True, "links": {"self": "http://example.com/rel/2/more"}}}
        )
        == expected
    )
