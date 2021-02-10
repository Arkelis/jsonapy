import pytest

from jsonapy import BaseResource
from jsonapy.document import JSONAPIDocument


class AResource(BaseResource):
    lastname: str
    id: int

    class Meta:
        resource_name = "resource"


AResource.register_link_factory("self", lambda x: str(x))


@pytest.fixture
def obj() -> AResource:
    return AResource(id=1, lastname="Doe")


@pytest.fixture
def document_obj(obj: AResource) -> JSONAPIDocument:
    return JSONAPIDocument(data=obj, required_attributes="__all__")


def test_document_simple_export(document_obj: JSONAPIDocument, obj: AResource):
    assert document_obj.jsonapi_dict() == {"data": obj.jsonapi_dict(required_attributes="__all__")}
