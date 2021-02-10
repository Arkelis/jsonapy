# Copyright (c) 2021 Guillaume Fayard
# This library is licensed under the MIT license
# For a complete copy of the license, see the LICENSE file.

""" # Complete reference of resource creation

## Fields

You can define the [fields](https://jsonapi.org/format/#document-resource-object-fields)
to export with annotations:

```python
class MyResource(BaseResource):
   id: int
   attr1: str
   attr2: bool
```

You must annotate the `id` member, even if it is only used for identification
prupose and not considered as an attribute.

A field cannot be named after reserved names which are:
- the already-defined members of the `BaseResource` class;
- `"type"`, reserved identifier object member. By default, the type name of
 the resource is the name of the class. It can be can overwritten by specifying
 the meta `resource_name` attribute
- `"links"`: a member name used by the JSON:API specification.
- `"relationships"`: a member name used by the JSON:API specification.

```python
class NamedResource(BaseResource):
   id: int

   class Meta:
        resource_name = "myResourceName"
```

## Link registering

To integrate the endpoints of an API in the resources, you can register
factories functions that will be used to produce resource's links. It can be
done in two ways:

- If the factory function does not use any dependency, it can be defined
directly in the `Meta` inner class:

```python
class LinkedResource(BaseResource):
   id: int

   class Meta:
        links_factories = {
            "self": lambda x: f"/linked/{x}"
        }
```

- If the model is imported in the module where routing functions are defined,
factories functions can be registered with a class method. For example, if
you are using [Starlette](https://www.starlette.io/), it could be:

```python
# app and routes definitions...

LinkedResource.register_link_factory("self", lambda x: app.url_path_for("linked_resource", x))
```

For the relationships links, prefix the links names with the relationship name:

```python
BResource.register_link_factory(
    "related__self",
    lambda x: f"/bresource/{x}/relationships/related"
)
```

See `BaseResource.register_link_factory()` for more information

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
When a resource subclasses another resource, all fields are copied to the sub-resource.

## Special class attributes

### Meta attributes defined in the `Meta` inner class

This inner class allows you to define several metadata

- `is_abstract`: a boolean indicating the model is aimed to be instantiated.
- `resource_name`: the resource type name
- `identifier_meta_fields`: a set containing extra non standard fields that
  contain extra meta-information.
- `links_factories`: a dictonary containing factories functions used to
  generate resources links when they are exported. The keys are the names of
  the links and the values their factories functions. The functions take the
  id of the exported object as unique argument and return an URL string.

During runtime, these metadata can be accessed by the special names
`__is_abstract__`, `__resource_name__`, `__identifier_meta_fields__` and
`__links_factories__` directly on the resource class. The `Meta` inner class
is not accessible during runtime.

### Atomic and relationships fields

When a field is a instance of `BaseResource`, it is considered as a
relationship field. The other fields are considered as "atomic": the `id` used
for identification, and the attributes that are exported in the `"attributes"`
object.

Some special attributes provide the sets of atomic and relationships fields names.

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
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import Literal
from typing import Optional
from typing import Set
from typing import TYPE_CHECKING
from typing import TypeVar
from typing import Union

from jsonapy import utils


__all__ = ("BaseResource", "BaseResourceMeta")

IdType = TypeVar("IdType")


class BaseResourceMeta(type):
    """Metaclass of resource classes.

    Instantiate a resource class and perform some initialization and checks.

    ###### Initialization ######

    The following class attributes are initialized here:

    - `__fields_types__`: an alias for `__annotations__`
    - `__atomic_fields_set__`: a set containing the names of fields whose type
      is not a instance of `BaseResourceMeta` (the names of the non resource
      fields).
    - `__relationships_fields_set__`: a set containing the names of the fields
      referring another resource.

    ###### Extraction of `Meta` attributes ######

    This metaclass converts the `Meta` inner class of the defined models into
    special attributes:

    - `__is_abstract__`: the `Meta.is_abstract` attribute if defined, else `True`.
    - `__resource_name__`: the `Meta.resource_name` attribute if defined, else
      the name of the resource class.
    - `__identifier_meta_fields__`: the `Meta.identifier_meta_fields` attribute
      if defined, else an empty set.
    - `__links_factories__`: the `Meta.links_factories` attribute if defined,
      else an empty dictionary. If a link name is not valid, a `ValueError` is
      raised.

    """

    def __new__(mcs, name, bases, namespace):
        try:
            meta = namespace.pop("Meta").__dict__
        except KeyError:
            meta = {}

        cls = super().__new__(mcs, name, bases, namespace)

        # forbidden fields, see https://jsonapi.org/format/#document-resource-object-fields
        forbidden_fields = {"type", "links", "relationships"}
        # identifier fields, see https://jsonapi.org/format/#document-resource-identifier-objects
        identifier_fields = {"type", "id"}

        cls.__annotations__ = {
            name: type_
            for klass in cls.mro()
            if isinstance(klass, BaseResourceMeta)
            for (name, type_) in klass.__annotations__.items()
        }

        # members special attributes
        annotations_items = cls.__annotations__.items()
        cls.__fields_types__ = cls.__annotations__
        cls.__atomic_fields_set__ = {
            name
            for name, type_ in annotations_items
            if not isinstance(type_, BaseResourceMeta)
        } - forbidden_fields
        cls.__relationships_fields_set__ = {
            name
            for name, type_ in annotations_items
            if isinstance(type_, BaseResourceMeta)
        }

        links_factories = {}
        for name, factory in meta.get("links_factories", {}):
            split_name = name.split("__")
            if len(split_name) > 1:
                relationship_name = split_name[0]
                if relationship_name not in cls.__relationships_fields_set__:
                    raise ValueError(f"'{relationship_name}' is not a valid relationship for {cls.__name__}.")
                links_factories[name] = factory

        # meta special attributes
        cls.__links_factories__ = links_factories
        cls.__is_abstract__ = meta.get("is_abstract", False)
        cls.__resource_name__ = meta.get("resource_name", cls.__name__)
        cls.__identifier_meta_fields__ = meta.get("identifier_meta_fields", set())

        if not cls.__is_abstract__ and "id" not in cls.__annotations__:
            raise AttributeError("A Resource must have an 'id' attribute.")

        # utilitarian private attributes
        cls._forbidden_fields = forbidden_fields
        cls._identifier_fields = identifier_fields

        return cls


class BaseResource(metaclass=BaseResourceMeta):
    """Base class for defining resources.

    See the top of the `jsonapy.base` module for an overview documentation.

    This class is instantiated by the `BaseResourceMeta` metaclass.
    This class contains public methods only. See the `_BaseResource` base class
    for the underlying implementation.
    """

    if TYPE_CHECKING:
        # for IDE, provided by metaclass
        __fields_types__: Dict[str, type]
        __atomic_fields_set__: Set[str]
        __relationships_fields_set__: Set[str]
        __resource_name__: str
        __is_abstract__: bool
        __identifier_meta_fields__: Set[str]
        __links_factories__: Dict[str, Callable[[IdType], str]]
        _identifier_fields: Set[str]
        _forbidden_fields: Set[str]

        # must be provided by subclasses
        id: IdType

    class Meta:
        is_abstract: bool = True
        resource_name: str
        identifier_meta_fields: Set[str]
        links_factories: Dict[str, Callable[[IdType], str]]

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

    ###########################################################################
    #                           P U B L I C   A P I                           #
    ###########################################################################

    def jsonapi_dict(
        self,
        required_attributes: Union[Iterable[str], Literal["__all__"]],
        links: Optional[Iterable[str]] = None,
        relationships: Optional[Dict] = None,
    ) -> Dict:
        """Export the object as a dictionary in compliance with JSON:API specification.

        ###### Parameters ######

        - `required_attributes`: a iterable containing the fields names to
        include in dumped data. If all fields are required, provide the
        `"__all__"` literal instead of an iterable.
        - `links`: an iterable of links names to include in data. You must have
        registered the link names before (see `BaseResource.register_link_factory()`
        method).
        - `relationships`: a dictionary specifying the relationships to include,
        if the identifier object must be exported, and which links must be dumped.
        The keys must be a attribute of the resource referencing another resource
        and the value of each key is another dict containing two keys:
          + `"data"`: a boolean indicating if an identifier object must be included
          + `"links"`: an iterable of links names to dump.

        For example, let's say an article is related to an author. The relationships dict could be:
        ```python
        {"author": {"data": True, "links": {"self"}}}
        ```

        ###### Returned value ######

        A dictionary representing the object according to the JSON:API
        specification.

        ###### Errors raised ######

        A `ValueError` is raised if:
        - An attribute name in `required_attributes` argument is invalid.
        - A link name in `links` argument is not registered.
        - A key of the `relationship` argument does not refer to a valid
        related resource.
        - A link name of a specified relationship is not registered.
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

    def dump(
        self,
        required_attributes: Union[Iterable[str], Literal["__all__"]],
        links: Optional[Dict] = None,
        relationships: Optional[Dict] = None,
        dump_function: Callable[[Dict], str] = json.dumps,
    ) -> str:
        """Call `jsonapi_dict()` method and dump the result with `dump_function`.

        ###### Parameters ######

        For a documentation about the `required_attributes`, `links`, `relationships`
        parameters, see `BaseResource.jsonapi_dict()` method.

        - `dump_function`: a function used to dump the dictionary returned by
        `jsonapi_dict()` method. By default, the dump function is `json.dumps()`.

        ###### Returned value ######

        A string dump of the JSON:API-compliant dictionary export of the object.

        ###### Error raised ######

        See `BaseResource.jsonapi_dict()`.
        """
        return dump_function(
            self.jsonapi_dict(required_attributes, links, relationships)
        )

    @classmethod
    def register_link_factory(cls, name: str, factory: Callable[[IdType], str]):
        """Add a link factory to the resource.

        When the resources are dump, these factories are used to produce their
        links. The factories are stored in the `__links_factories__` class
        attribute.

        ###### Parameters ######

        - `name`: the name of the link (for example `"self"`)
        - `factory`: a callable taking the id of the resource as parameter and
        returning a string representing the url to dump.

        To register a link name of a relationship, prefix the link name with
        the attribute name and two underscores. For example, if an `"article"`
        resource has an `"author"` relationship attribute, you can register
        `"author__self"` or `"author__related"` links.

        ###### Returned value ######

        `None`

        ###### Errors raised ######

        If the relationship does not exist, raise a `ValueError`.
        """
        split_name = name.split("__")
        if len(split_name) > 1:
            relationship_name = split_name[0]
            if relationship_name not in cls.__relationships_fields_set__:
                raise ValueError(f"'{relationship_name}' is not a valid relationship for {cls.__name__}.")
        cls.__links_factories__[name] = factory

    ###########################################################################
    #                                                                         #
    #                          P R I V A T E   A P I                          #
    #        ( U N D E R L Y I N G   I M P L E M E N E N T A T I O N )        #
    #                                                                         #
    ###########################################################################

    ###########################################################################
    #                  P R O P E R T I E S   A N D   U T I L S                #
    ###########################################################################

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

    ###########################################################################
    #                           V A L I D A T I O N                           #
    ###########################################################################

    @classmethod
    def _validate_relationships(cls, relationships: Dict) -> None:
        """Make sure that the provided `relationships` dictionary is valid

        - The keys must refer an existing relationships field.
        - The values must contain at least a data or a links member.

        Raise a `ValueError` if the dictionary is not valid.
        """
        errors = []
        for name, rel_dict in relationships.items():
            if name not in cls.__relationships_fields_set__:
                errors.append(f"    '{name}' is not a valid relationship.")
            if (rel_dict.get("links") is None and rel_dict.get("data")) is None:
                errors.append(
                    f"    You must provide at least links or data for the '{name}' relationship."
                )
        if errors:
            raise ValueError("\n" + "\n".join(errors))

    @classmethod
    def _validate_links(cls, links, relationship: Optional[str] = None):
        """Make sure that the links are registered in the resource class.

        Check if the passed names are keys of the __links_factories__ speciak
        attribute. If at least a name is not present, raise a `ValueError`.
        """
        links = {cls._qualname(name, relationship) for name in links}
        errors = []
        for name in links:
            if name not in cls.__links_factories__:
                errors.append(f"    '{name}' is not a registered link name.")
        if errors:
            raise ValueError("\n" + "\n".join(errors))

    ###########################################################################
    #            F O R M A T T I N G   A N D   F I L T E R I N G              #
    ###########################################################################

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

    def _make_links(self, links: Iterable[str], relationship: Optional[str] = None):
        return {
            name: self.__links_factories__[self._qualname(name, relationship)](self.id)
            for name in links
        }
