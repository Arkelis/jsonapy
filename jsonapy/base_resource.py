import json
from collections import Iterable
from typing import Callable
from typing import Dict
from typing import Literal
from typing import Set
from typing import TYPE_CHECKING
from typing import Union

from jsonapy import utils


class BaseResourceMeta(type):
    def __new__(mcs, name, bases, namespace):  # noqa C901
        cls = super().__new__(mcs, name, bases, namespace)

        annotations_items = cls.__annotations__.items()
        cls.__fields_types__ = cls.__annotations__
        cls.__atomic_fields_set__ = {
            name
            for name, type_ in annotations_items
            if not issubclass(type_, BaseResource)
        }
        cls.__relationships_fields_set__ = {
            name
            for name, type_ in annotations_items
            if issubclass(type_, BaseResource)
        }

        return cls


class BaseResource(metaclass=BaseResourceMeta):
    if TYPE_CHECKING:
        # for IDE
        __fields_types__: Dict[str, type]
        __atomic_fields_set__: Set[str]
        __relationships_fields_set__: Set[str]

    @property
    def id(self):
        raise NotImplementedError

    class Meta:
        resource_name: str

    def jsonapi_dict(self, required_attributes, links, relationships):
        """Dump the object as JSON in compliance with JSON:API specification.

        Parameters

        - `links`: a dictionary containing the links to include in data. For example::
            {
                "self": request.url_for(...),
                "related": request.url_for(...),
            }
        if using FastAPI / Starlette.
        - `required_attributes`: a iterable containing the fields names to include in dumped data. If all fields are
        required, provide the `"__all__"` literal instead of an iterable.
        - `relationships`: a dictionary specifying the relationships to include and their fields and links.
        The keys must be a attribute of the resource referencing another resource. The value is another dict containing
        two keys:
            + `fields`: a list containing the fields to dump (see required_attributes above)
            + `links`: a dict containing the links to dump (see links parameter above)
        For example, let's say an article is related to an author. The relationships dict could be::
            {
                "author": {
                    "field": ["id", "name"]
                    "links": {"self": request.url_for(...), ...}
                }
            }
        """
        data = {
            "type": self.Meta.resource_name,
            "id": self.id,
            "attributes": self.filtered_attributes(required_attributes),
        }
        if links:
            data["links"] = links
        if relationships:
            self.validate_relationships(relationships)
            data["relationships"] = self.formatted_relationships(relationships)
        return data

    def filtered_attributes(self, required_attributes: Union[Iterable, Literal["__all__"]]):
        if required_attributes == "__all__":
            required_attributes = self.__atomic_fields_set__
        return {
            utils.snake_to_camel_case(k): v
            for (k, v) in self.__dict__.items()
            if k in required_attributes
        }

    def validate_relationships(self, relationships):
        errors = []
        for name, rel_dict in relationships.items():
            if name not in self.__relationships_fields_set__:
                errors.append(f"'{name}' is not a valid relationship.")
            if (rel_dict.get("links") is None and rel_dict.get("fields")) is None:
                errors.append(f"You must provide at least links or fields for the '{name}' relationship.")
        if errors:
            raise ValueError("\n".join(errors))

    def formatted_relationships(self, relationships):
        relationships_dict = {}
        for name, rel_payload in relationships.items():
            related_object: BaseResource = self.__dict__[name]
            if related_object is None:
                relationships_dict[utils.snake_to_camel_case(name)] = None
                continue
            rel_data = {}
            if rel_payload.get("fields") is not None:
                rel_data["data"] = related_object.filtered_attributes(rel_payload["fields"])
            if rel_payload.get("links") is not None:
                rel_data["links"] = rel_payload["links"]
            relationships_dict[utils.snake_to_camel_case(name)] = rel_data
        return relationships_dict

    def dump(self, required_attributes, links, relationships, dump_function: Callable[[Dict], str] = json.dumps) -> str:
        return dump_function(self.jsonapi_dict(required_attributes, links, relationships))
