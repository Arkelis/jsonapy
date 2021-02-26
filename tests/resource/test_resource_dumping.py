import json
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import Optional
from typing import Union

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
    optional_attr: Optional[str]
    default_attr: Optional[str] = "default"

    class Meta:
        resource_name = "more"


class RelatedResource(BaseResource):
    related_more: MoreAttributes
    id: int
    foo: str

    class Meta:
        resource_name = "related"


class RelatedIterableResource(BaseResource):
    related_more: Iterable[MoreAttributes]
    id: int


class ResourceWithComplexAttribute(BaseResource):
    id: int
    simple_attr: str
    complex_attr: Union[int, str, bool]
    union_without_none: Union[int, str]
    other: Dict[Any, Any]


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


@pytest.fixture
def related_object_none() -> RelatedResource:
    return RelatedResource(related_more=None, id=3, foo="baz")


@pytest.fixture
def related_object_iterable() -> RelatedIterableResource:
    return RelatedIterableResource(related_more=[
        MoreAttributes(id=1, last_name="Last", name="Name", birth_date=1991),
        MoreAttributes(id=2, last_name="Last", name="Name", birth_date=1991)
    ], id=3, foo="baz")


@pytest.fixture
def empty_object() -> ResourceWithComplexAttribute:
    return ResourceWithComplexAttribute()


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


def test_invalid_link(simple_object: SimpleResource):
    with pytest.raises(ValueError) as err:
        simple_object.jsonapi_dict(
            required_attributes="__all__",
            links={"invalid"}
        )

    assert str(err.value) == "\n    'invalid' is not a registered link name."


def test_simple_dumping_with_filtered_attrs(more_object: MoreAttributes):
    expected = {
        "type": "more",
        "id": 1,
        "attributes": {"birthDate": 1991},
    }
    assert more_object.jsonapi_dict(required_attributes=["birth_date"]) == expected


def test_simple_dumping_optional_attr(more_object: MoreAttributes):
    expected = {
        "type": "more",
        "id": 1,
        "attributes": {
            "birthDate": 1991,
            "optionalAttr": None,
            "defaultAttr": "default"}}

    assert (more_object.jsonapi_dict(
                required_attributes=["birth_date", "optional_attr", "default_attr"])
            == expected)


def test_simple_dumping_unexpected_attribute(more_object: MoreAttributes):
    with pytest.raises(ValueError) as err:
        more_object.jsonapi_dict(required_attributes=["invalid"])

    assert str(err.value) == "\n    Unexpected required attribute: 'invalid'."


def test_dumping_without_id(empty_object: ResourceWithComplexAttribute):
    with pytest.raises(AttributeError) as err:
        empty_object.jsonapi_dict("__all__")

    assert str(err.value) == "This 'ResourceWithComplexAttribute' object has no id."


def test_missing_argument(empty_object: ResourceWithComplexAttribute):
    empty_object.id = 1

    # this covers utils.is_an_optional_field
    with pytest.raises(ValueError) as err:
        empty_object.jsonapi_dict("__all__")

    assert (
        "Missing required attribute: 'other'." in str(err.value)
        and "Missing required attribute: 'complex_attr'." in str(err.value)
        and "Missing required attribute: 'union_without_none'." in str(err.value)
        and "Missing required attribute: 'simple_attr'." in str(err.value)
    )


def test_invalid_relationship(simple_object: SimpleResource):
    with pytest.raises(ValueError) as err:
        simple_object.jsonapi_dict(
            required_attributes="__all__",
            relationships={"foo": {"data": True}},
        )

    assert str(err.value) == "\n    'foo' is not a valid relationship."


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


def test_relationship_none(related_object_none: RelatedResource):
    expected = {
        "type": "related",
        "id": 3,
        "attributes": {"foo": "baz"},
        "relationships": {
            "related_more": None
        }
    }
    assert (
        related_object_none.jsonapi_dict(
            required_attributes="__all__",  # __all__ even if no attribute
            relationships={"related_more": {"data": True, "links": {"related"}}}
        )
        == expected
    )


def test_relationship_iterable(related_object_iterable: RelatedResource):
    expected = {
        "type": "RelatedIterableResource",
        "id": 3,
        "relationships": {
            "related_more": {
                "data": [{"type": "more", "id": 1},
                         {"type": "more", "id": 2}],
            }
        }
    }
    assert (
        related_object_iterable.jsonapi_dict(
            required_attributes="__all__",
            relationships={"related_more": {"data": True, "links": {}}}
        )
        == expected
    )


def test_relationship_invalid_options(related_object: RelatedResource):
    with pytest.raises(ValueError) as err:
        related_object.jsonapi_dict(
            required_attributes="__all__",
            relationships={"related_more": {"foo": "bar"}}
        )

    assert str(err.value) == "\n    You must provide at least links or data for the 'related_more' relationship."


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
