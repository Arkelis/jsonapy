# Copyright (c) 2021 Guillaume Fayard
# This library is licensed under the MIT license
# For a complete copy of the license, see the LICENSE file.

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
        resource_name = "myResourceName"
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

## Link registering

To integrate the endpoints of your API in the resources, you can register links
factories function that will be used to produce resource's links.

```python
BResource.register_link_factory("self", lambda x: f"/bresource/{x}")
```

For the relationships links, prefix the links names with the relationship name:

```python
BResource.register_link_factory(
    "related__self",
    lambda x: f"/bresource/{x}/relationships/related"
)
```

The links factories can be accessed by the `__links_factories__` special
attribute. See `BaseResource.register_link_factory`.
"""


import json
from typing import Iterable
from typing import Callable
from typing import Dict
from typing import Literal
from typing import Optional
from typing import Set
from typing import TYPE_CHECKING
from typing import TypeVar
from typing import Union

from jsonapy import utils


__all__ = ("BaseResource", "BaseResourceMeta")

IdType = TypeVar("IdType")


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
        __links_factories__: Dict[str, Callable[[IdType], str]]

        # must be provided by subclasses
        id: IdType

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

    @staticmethod
    def _qualname(name: str, relationship: Optional[str] = None):
        return f"{relationship}__{name}" if relationship else name


class BaseResourceMeta(type):
    """Metaclass of resource classes.

    This metaclass converts the `Meta` inner class of the defined models into
    special attributes:

    - `__is_abstract__`: a boolean indicating the model is aimed to be instantiated.
    - `__resource_name__`: the resource type name
    - `__identifier_meta_fields__`: a set containing extra non standard fields that
      contain extra meta-information

    Moreover, it initialize an empty `__links_factories__` dictionary. It will contain
    the links names as keys and their factory functions as values.
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
        cls.__links_factories__ = {}

        if not cls.__is_abstract__ and "id" not in cls.__annotations__:
            raise AttributeError("A Resource must have an 'id' attribute.")

        return cls


class BaseResource(_BaseResource, metaclass=BaseResourceMeta):
    """Base class for defining resources.

    See the top of the `jsonapy.base` module for an overview documentation.

    This class is instantiated by the `BaseResourceMeta` metaclass.
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
        links: Optional[Iterable[str]] = None,
        relationships: Optional[Dict] = None,
    ) -> Dict:
        """Export the object as a dictionary in compliance with JSON:API specification.

        **Parameters**

        - `required_attributes`: a iterable containing the fields names to
        include in dumped data. If all fields are required, provide the
        `"__all__"` literal instead of an iterable.
        - `links`: an iterable of links names to include in data. You must have
        registered the link names before (see `BaseResource.register_link_factory()`
        method).
        - `relationships`: a dictionary specifying the relationships to include
        and their fields and links. The keys must be a attribute of the resource
        referencing another resource. The value is another dict containing two
        keys:
          + `data`: a boolean indicating if an identifier object must be included
          + `links`: an iterable of links names to dump

        For example, let's say an article is related to an author. The relationships dict could be:
        ```python
        {"author": {"data": True, "links": {"self"}}}
        ```
        """
        data = {
            "type": self.__resource_name__,
            "id": self.id,
            "attributes": self._filtered_attributes(required_attributes),
        }
        if links:
            self._validate_links(links)
            data["links"] = self._make_links(links)
        if relationships:
            self._validate_relationships(relationships)
            data["relationships"] = self._formatted_relationships(relationships)
        return data

    def _filtered_attributes(
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

    def _validate_links(self, links, relationship: Optional[str] = None):
        if relationship is not None:
            links = {f"{relationship}__{name}" for name in links}
        errors = []
        for name in links:
            if name not in self.__links_factories__:
                errors.append(f"    '{name}' is not a registered link name.")
        if errors:
            raise ValueError("\n" + "\n".join(errors))

    def _make_links(self, links: Iterable[str], relationship: Optional[str] = None):
        return {
            name: self.__links_factories__[self._qualname(name, relationship)](self.id)
            for name in links
        }

    def _validate_relationships(self, relationships: Dict) -> None:
        """Make sure that the provided `relationships` dictionary is valid

        - The keys must refer an existing relationships field.
        - The values must contain at least a data or a links member.

        Raise a `ValueError` if the dictionary is not valid.
        """
        errors = []
        for name, rel_dict in relationships.items():
            if name not in self.__relationships_fields_set__:
                errors.append(f"    '{name}' is not a valid relationship.")
            if (rel_dict.get("links") is None and rel_dict.get("data")) is None:
                errors.append(
                    f"    You must provide at least links or data for the '{name}' relationship."
                )
        if errors:
            raise ValueError("\n" + "\n".join(errors))

    def _formatted_relationships(self, relationships: Dict) -> Dict:
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
            relationships_link = rel_payload.get("links")
            if relationships_link is not None:
                self._validate_links(rel_payload["links"], relationship=name)
                rel_data["links"] = self._make_links(rel_payload["links"], relationship=name)
            relationships_dict[name] = rel_data
        return relationships_dict

    def dump(
        self,
        required_attributes: Union[Iterable[str], Literal["__all__"]],
        links: Optional[Dict] = None,
        relationships: Optional[Dict] = None,
        dump_function: Callable[[Dict], str] = json.dumps,
    ) -> str:
        """Call `jsonapi_dict()` method and dump the result with `dump_function`.

        By default, the used dump function is `json.dumps()`.
        """
        return dump_function(
            self.jsonapi_dict(required_attributes, links, relationships)
        )

    @classmethod
    def register_link_factory(cls, name: str, factory: Callable[[IdType], str]):
        """Add a link factory to the resource.

        When the resources are dump, these factories are used to produce their
        links. The factories are stored in the `__links_factories__`
        dictionary.

        **Parameters**

        - `name`: the name of the link (for example `"self"`)
        - `factory`: a callable taking the id of the resource as parameter and
        returning a string representing the url to dump.

        To register a link name of a relationship, prefix the link name with
        the attribute name and two underscores. For example, if an `"article"`
        resource has an `"author"` relationship attribute, you can register
        `"author__self"` or `"author__related"` links.

        If the relationship does not exist, raise a `ValueError`.
        """
        split_name = name.split("__")
        if len(split_name) > 1:
            relationship_name = split_name[0]
            if relationship_name not in cls.__relationships_fields_set__:
                raise ValueError(f"'{relationship_name}' is not a valid relationship for {cls.__name__}.")
        cls.__links_factories__[name] = factory
