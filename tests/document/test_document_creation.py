from typing import List

import pytest

from jsonapy import BaseResource
from jsonapy.document import JSONAPIDocument


class AResource(BaseResource):
    lastname: str
    id: int

    class Meta:
        resource_name = "resource"


@pytest.fixture
def obj() -> AResource:
    return AResource(id=1, lastname="Doe")


@pytest.fixture
def obj_list(obj: AResource) -> List[AResource]:
    return [AResource(id=2, lastname="Smith"), obj]


AResource.register_link_factory("self", lambda x: str(x))


def test_document_creation(obj: AResource):
    document = JSONAPIDocument(
        data=obj,
        required_attributes="__all__",
        resource_links={"self"}
    )
    assert document.data_export_options == {
        "required_attributes": "__all__",
        "links": {"self"},
        "relationships": None
    }
    assert document.data == obj


def test_document_data_list_creation(obj_list: AResource):
    document = JSONAPIDocument(
        data=obj_list,
        required_attributes="__all__",
        resource_links={"self"}
    )
    assert document.data_export_options == {
        "required_attributes": "__all__",
        "links": {"self"},
        "relationships": None
    }
    assert document.data == obj_list
