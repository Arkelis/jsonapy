# Copyright (c) 2021 Guillaume Fayard
# This library is licensed under the MIT license
# For a complete copy of the license, see https://pycolore.mit-license.org/

"""# Complete reference of resource creation

## Attributes

You can define the attributes to export with annotations:

```python
class MyResource(BaseResource):
   id: int
   attr1: str
   attr2: bool
```

An attribute cannot be named after reserved names that are:
- the already-defined members of the `BaseResource` class;
- `"type"`, reserved identifier object member. By default, the type name of
 the resource is the name of the class. You can override it by specifying
 the meta resource_name attribute

```python
class NamedResource(BaseResource):
   id: int

   class Meta:
        resource_name = "my resource name"
```

## Abstract resource and inheritance

A resource must export an `"id"` member, unless it is an abstract resource.
An abstract resource can be inherited to create concrete resources, we indicate
that a resource is abstract with the `Meta` innerclass:

```python
class AbstractResource(BaseResource):
    attr: str

    class Meta:
        is_abstract = True
```

A concrete resource definition without `"id"` member will raise an `AttributeError`.
When a resource subclasses another resource, all attributes are copied to the sub-resource.

## The `Meta` inner class

This inner class allows you to define several metadata

- `is_abstract`: a boolean indicating the model is aimed to be instantiated.
- `resource_name`: the resource type name
- `identifier_meta_fields`: a set containing extra non standard fields that
  contain extra meta-information.

During runtime, these metadata can be accessed by the special names `__is_abstract__`,
`__resource_name__` and `__identifier_meta_fields__` directly on the resource class.
The `Meta` inner class is not accessible during runtime.

## Atomic and relationships fields

When an attribute is a instance of `BaseResource`, it is considered as a relationship field.
The other attributes are considered as "atomic" (they simply appear in the `"attributes"` object
in JSON:API).

Some special attributes provide the sets of atomic and relationships fields.

```python
class AResource(BaseResource):
    id: int


class BResource(BaseResource):
    id: int
    name: str
    related: AResource
```

```pycon
>>> BResource.__fields_types__
{'id': int, 'name': str, 'related': __main__.AResource}
>>> BResource.__atomic_fields_set__
{'id', 'name'}
>>> BResource.__relationships_fields_set__
{'related'}
```
"""


import json
from typing import Iterable
from typing import Any
from typing import Callable
from typing import Dict
from typing import Literal
from typing import Optional
from typing import Set
from typing import TYPE_CHECKING
from typing import Union

from jsonapy import utils


class _BaseResource:
    """Private base class of BaseResource containing some special utilitarian methods."""
    if TYPE_CHECKING:
        # for IDE
        __fields_types__: Dict[str, type]
        __atomic_fields_set__: Set[str]
        __relationships_fields_set__: Set[str]
        __resource_name__: str
        __is_abstract__: bool
        __identifier_meta_fields__: Set[str]

        # must be provided by subclasses
        id: Any

    __annotations__ = {}
    _forbidden_fields = {"type", "links", "relationships"}
    _identifier_fields = {"type", "id"}

    def __init_subclass__(cls, **kwargs):
        cls.__annotations__ = {
            name: type_
            for klass in cls.mro()
            if issubclass(klass, _BaseResource)
            for (name, type_) in klass.__annotations__.items()
        }

        annotations_items = cls.__annotations__.items()
        cls.__fields_types__ = cls.__annotations__
        cls.__atomic_fields_set__ = {
            name
            for name, type_ in annotations_items
            if not issubclass(type_, _BaseResource)
        } - _BaseResource._forbidden_fields
        cls.__relationships_fields_set__ = {
            name
            for name, type_ in annotations_items
            if issubclass(type_, _BaseResource)
        }

    @property
    def _identifier_dict(self):
        identifier_dict = {
            "type": self.__resource_name__,
            "id": self.id,
        }
        if self.__identifier_meta_fields__:
            identifier_dict["meta"] = {name: getattr(self, name) for name in self.__identifier_meta_fields__}
        return identifier_dict


class BaseResourceMeta(type):
    """Metaclass of resource classes.

    This metaclass converts the `Meta` inner class of the defined models into
    sepcial attributes:

    - `__is_abstract__`: a boolean indicating the model is aimed to be instantiated.
    - `__resource_name__`: the resource type name
    - `__identifier_meta_fields__`: a set containing extra non standard fields that
      contain extra meta-information
    """

    def __new__(mcs, name, bases, namespace):
        try:
            meta = namespace.pop("Meta").__dict__
        except KeyError:
            meta = {}

        cls = super().__new__(mcs, name, bases, namespace)

        cls.__is_abstract__ = meta.get("is_abstract", False)
        cls.__resource_name__ = meta.get("resource_name", cls.__name__)
        cls.__identifier_meta_fields__ = meta.get("identifier_meta_fields", set())

        if not cls.__is_abstract__ and "id" not in cls.__annotations__:
            raise AttributeError("A Resource must have an 'id' attribute.")

        return cls


class BaseResource(_BaseResource, metaclass=BaseResourceMeta):
    """Base class for defining resources.

    See the top of the `jsonapy.base` module for overview documentation.
    """

    class Meta:
        is_abstract = True
        resource_name: str
        identifier_meta_fields: Set[str]

    def __init__(self, **kwargs):
        """Automatically set all passed arguments.

        Take keyword arguments only and raise a `ValueError` if a parameter
        tries to reassign an already defined member (like the `jsonapi_dict()`
        method).
        """
        errors = []
        for name in kwargs:
            if hasattr(self, name) or name in self._forbidden_fields:
                errors.append(f"    This attribute name is reserved: '{name}'.")
        missing_arguments = set(self.__fields_types__) - set(kwargs)
        if missing_arguments:
            errors.extend(f"    Missing argument: '{arg}'." for arg in missing_arguments)
        if errors:
            raise ValueError("\n" + "\n".join(errors))
        for k, v in kwargs.items():
            setattr(self, k, v)

    def jsonapi_dict(
        self,
        required_attributes: Union[Iterable[str], Literal["__all__"]],
        links: Optional[Dict] = None,
        relationships: Optional[Dict] = None,
    ):
        """Dump the object as JSON in compliance with JSON:API specification.

        Parameters

        - `required_attributes`: a iterable containing the fields names to include in dumped data. If all fields are
        required, provide the `"__all__"` literal instead of an iterable.
        - `links`: a dictionary containing the links to include in data. For example:
        ```python
        {"self": request.url_for(...), "related": request.url_for(...)}
        ```
        if using [FastAPI](https://fastapi.tiangolo.com/) or
        [Starlette](https://www.starlette.io).
        - `relationships`: a dictionary specifying the relationships to include and their fields and links.
        The keys must be a attribute of the resource referencing another resource. The value is another dict containing
        two keys:
          + `data`: a boolean indicating if an identifier object must be included
          + `links`: a dict containing the links to dump (see links parameter above)

        For example, let's say an article is related to an author. The relationships dict could be:
        ```python
        {
            "author": {
                "data": True
                "links": {"self": request.url_for(...)}
            }
        }
        ```
        """
        data = {
            "type": self.__resource_name__,
            "id": self.id,
            "attributes": self.filtered_attributes(required_attributes),
        }
        if links:
            data["links"] = links
        if relationships:
            self.validate_relationships(relationships)
            data["relationships"] = self.formatted_relationships(relationships)
        return data

    def filtered_attributes(
        self, required_attributes: Union[Iterable, Literal["__all__"]]
    ) -> Dict:
        """Filter the attributes with provided `required_attributes` iterable.

        If a member of the iterable is not in the annotated attributes, raise a
        `ValueError`. The names are converted from snake case to camel case.
        """
        if required_attributes == "__all__":
            required_attributes = self.__atomic_fields_set__
        unexpected_attributes = set(required_attributes) - self.__atomic_fields_set__
        if unexpected_attributes:
            raise ValueError(
                "\n"
                + "\n".join(
                    f"Unexpected required attribute: '{name}'"
                    for name in unexpected_attributes
                )
            )
        return {
            utils.snake_to_camel_case(k): v
            for (k, v) in self.__dict__.items()
            if k in set(required_attributes) - self._identifier_fields
        }

    def validate_relationships(self, relationships: Dict) -> None:
        """Make sure that the provided `relationships` dictionary is valid

        - The keys must refer an existing relationships field.
        - The values must contain at least a data or a links member.

        Raise a `ValueError` if the dictionary is not valid.
        """
        errors = []
        for name, rel_dict in relationships.items():
            if name not in self.__relationships_fields_set__:
                errors.append(f"'{name}' is not a valid relationship.")
            if (rel_dict.get("links") is None and rel_dict.get("data")) is None:
                errors.append(
                    f"You must provide at least links or data for the '{name}' relationship."
                )
        if errors:
            raise ValueError("\n".join(errors))

    def formatted_relationships(self, relationships: Dict) -> Dict:
        """Format relationships into the JSON:API format."""
        relationships_dict = {}
        for name, rel_payload in relationships.items():
            related_object: BaseResource = self.__dict__[name]
            if related_object is None:
                relationships_dict[name] = None
                continue
            rel_data = {}
            if rel_payload.get("data"):
                rel_data["data"] = related_object._identifier_dict
            if rel_payload.get("links") is not None:
                rel_data["links"] = rel_payload["links"]
            relationships_dict[name] = rel_data
        return relationships_dict

    def dump(
        self,
        required_attributes: Union[Iterable[str], Literal["__all__"]],
        links: Optional[Dict] = None,
        relationships: Optional[Dict] = None,
        dump_function: Callable[[Dict], str] = json.dumps,
    ) -> str:
        """Call `BaseResource.jsonapi_dict()` method and dump the result with dump_function.

        By default, the used dump function is `json.dumps()`.
        """
        return dump_function(
            self.jsonapi_dict(required_attributes, links, relationships)
        )