# Copyright (c) 2021 Guillaume Fayard
# This library is licensed under the MIT license
# For a complete copy of the license, see the LICENSE file.

""" # Complete reference of resource definition

This section explains how to define a resource, its fields and its links. See
`BaseResource.jsonapi_dict()` for a documentation on exporting objects into
JSON:API format.

## Fields

### Attributes

You can define the [fields](https://jsonapi.org/format/#document-resource-object-fields)
to export with annotations:

```python
from jsonapy import BaseResource


class MyResource(BaseResource):
   id: int
   attr1: str
   attr2: bool
```

You must annotate the `id` member, even if it is only used for identification
and not considered as an attribute.

A field cannot be named after reserved names which are:
- the already-defined members of the `BaseResource` class;
- `"type"`, a reserved identifier object member. By default, the type name of
 the resource is the name of the class. It can be can overwritten by specifying
 the `resource_name` attribute of the `Meta` inner class:

```python
class NamedResource(BaseResource):
   id: int

   class Meta:
        resource_name = "myResourceName"
```

- `"links"`: a member name used by the JSON:API specification.
- `"relationships"`: a member name used by the JSON:API specification.

### Relationships

When a field has a resource class type hint, it is considered as a relationship.

```python
class MyOtherResource(BaseResource):
   id: int
   related_main_resource: MyResource
```

The `related_main_resource` is a relationship and will be correctly handled
when dumping the instances. See `BaseResource.jsonapi_dict()` for more the
documentation on exporting the objects into JSON:API format.

### Meta fields

The `Meta` inner class lets you define non-standard attributes:

* `meta_attributes`: A set of meta attributes names. These attributes will
be exported in the [`meta`](https://jsonapi.org/format/#document-meta)
object (alongside `"id"`, `"type"`, `"attributes"`, `"relationships"` and `"links"`).
* `identifier_meta_attributes`: A set of identifier meta fields names,
these will be in the `meta` object when exporting
[resource identifier objects](https://jsonapi.org/format/#document-resource-identifier-objects)
(alongside `"type"` and `"id"`).

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
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routes import Route
from functools import partial

def linke_resource(request):
    ...

app = Starlette(debug=True, routes=[
    Route('/linked/{id}', linked_resources),
])

def make_link(route, request **path_params):
    return Request.url_for(request, route, **path_params)

LinkedResource.register_link_factory("self", partial(make_link, "linked_resources"))
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
When a resource subclasses another resource, all fields are copied to the sub-resource,
but the `Meta` inner class is not inherited, so a resource is concrete by default.

## Accessing configuration and meta information about resources

These resource classes are used in the following examples.

```python
class AResource(BaseResource):
    id: int


class BResource(BaseResource):
    id: int
    name: str
    related: AResource

    class Meta:
        links_factories = {
            "self": lambda x: f"/b/{x}",
            "related__self": lambda x: f"/b/{x}/relationships/related"}
```

### Basic information about fields

Some metadata about a resource can be accessed through top level functions applied on
a resource class:

```python
from jsonapy.functions import fields_types, relationships_names, attributes_names
fields_types(BResource)
# {'id': int, 'name': str, 'related': __main__.AResource}
relationships_names(BResource)
# {'related'}
attributes_names(BResource)
# {'name'}
```

See the `jsonapy.functions` module for more information about these functions
and refer to the following sections to know more about special metadata class
attributes.

### Atomic and relationships fields

When a field is a instance of `BaseResource`, it is considered as a
relationship field. The other fields are considered as "atomic": the `id` used
for identification, and the attributes that are exported in the `"attributes"`
object.

Some special attributes provide the sets of atomic and relationships fields names.

```python
BResource.__fields_types__
# {'id': int, 'name': str, 'related': __main__.AResource}
BResource.__atomic_fields_set__
# {'id', 'name'}
BResource.__relationships_fields_set__
# {'related'}
```

### Configuration special attributes

Summary of attributes which can be defined in the `Meta` inner class:

- `is_abstract`: A boolean indicating the model is aimed to be instantiated.
- `resource_name`: The resource type name.
- `meta_attributes`: A set of non-standard attributes names which will be
   exported in the [`meta`](https://jsonapi.org/format/#document-meta) object.
- `identifier_meta_attributes`: A set containing extra non standard fields
   names that contain extra meta-information for identification.
- `links_factories`: A dictonary containing factories functions used to
  generate resources links when they are exported. The keys are the names of
  the links and the values their factories functions.

During runtime, these metadata can be accessed with special attributes directly
on the resource classes. For example, the value of `is_abstract` is available
on the `__is_abstract__` attribute. The `Meta` inner class is not accessible
during runtime. See the `BaseResourceMeta` metaclass for more information about
these attributes initialization.

## Creating a resource class dynamically

This module provides a `create_resource()` functions for creating resources
classes at runtime. We can recreate `BResource`:

```python
BResource = create_resource(
    "BResource",
    {"links_factories":
     {"self": lambda x: f"/b/{x}",
      "related__self": lambda x: f"/b/{x}/relationships/related"}},
    id=int,
    name=str,
    related=AResource)

attributes_names(BResource)
# {'name'}
relationships_names(BResource)
# {'related'}
fields_types(BResource)
# {'id': int, 'name': str, 'related': __main__.AResource}
BResource.__links_factories__
# {'self': <function __main__.<lambda>(x)>,
#  'related__self': <function __main__.<lambda>(x)>}
```
"""

import collections.abc
import copy
import json
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import Literal
from typing import Mapping
from typing import Optional
from typing import Set
from typing import TYPE_CHECKING
from typing import Tuple
from typing import Type
from typing import TypeVar
from typing import Union

from jsonapy import utils


__all__ = ("BaseResource", "create_resource", "BaseResourceMeta")


def _validate_link_name(klass, name):
    """Check if the link name is consistent with the resource class.

    If the link name is a relationship-qualified name, check if the
    relationship exists. Else raise a `ValueError`.
    """
    split_name = name.split("__")
    if len(split_name) > 1:
        relationship_name = split_name[0]
        if relationship_name not in klass.__relationships_fields_set__:
            raise ValueError(f"'{relationship_name}' is not a valid relationship for {klass.__name__}.")


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

    - `__is_abstract__`: the `Meta.is_abstract` attribute if defined, else `False`.
    - `__resource_name__`: the `Meta.resource_name` attribute if defined, else
      the name of the resource class.
    - `__identifier_meta_attributes__`: the `Meta.identifier_meta_attributes` attribute
      if defined, else an empty set.
    - `___meta_attributes__`: the `Meta.meta_attributes` attribute if defined,
      else an empty set.
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
            if not utils.is_type_hint_instance_of(type_, mcs)
        } - forbidden_fields
        cls.__relationships_fields_set__ = {
            name
            for name, type_ in annotations_items
            if utils.is_type_hint_instance_of(type_, mcs)
        }

        links_factories = {}
        for name, factory in meta.get("links_factories", {}).items():
            _validate_link_name(cls, name)
            links_factories[name] = factory

        # meta special attributes
        cls.__links_factories__ = links_factories
        cls.__is_abstract__ = meta.get("is_abstract", False)
        cls.__resource_name__ = meta.get("resource_name", cls.__name__)
        cls.__identifier_meta_attributes__ = set(meta.get("identifier_meta_attributes", set()))
        cls.__meta_attributes__ = set(meta.get("meta_attributes", set()))

        if not cls.__is_abstract__ and "id" not in cls.__annotations__:
            raise AttributeError("A Resource must have an 'id' attribute.")

        # utilitarian private attributes
        cls._forbidden_fields = forbidden_fields
        cls._identifier_fields = identifier_fields

        return cls


class BaseResource(metaclass=BaseResourceMeta):
    """Base class for defining resources.

    See the top of the `jsonapy.base` module for a doumentation on resource
    definition.

    This class is instantiated by the `BaseResourceMeta` metaclass.
    """

    if TYPE_CHECKING:
        # for IDE, provided by metaclass
        __fields_types__: Dict[str, type]
        __atomic_fields_set__: Set[str]
        __relationships_fields_set__: Set[str]
        __resource_name__: str
        __is_abstract__: bool
        __identifier_meta_attributes__: Set[str]
        __links_factories__: Dict[str, Callable[..., str]]
        _identifier_fields: Set[str]
        _forbidden_fields: Set[str]

        # must be provided by subclasses
        id: Any

    class Meta:
        is_abstract: bool = True
        resource_name: str
        identifier_meta_attributes: Set[str]
        links_factories: Dict[str, Callable[..., str]]

    def __init__(self, **kwargs):
        """Automatically set all passed arguments.

        Take keyword arguments only and raise a `ValueError` if a parameter
        tries to reassign an already defined member (like the `jsonapi_dict()`.
        """
        errors = []
        for name in kwargs:
            if (hasattr(self, name) and name not in self.__fields_types__
                    or name in self._forbidden_fields):
                errors.append(f"    This attribute name is reserved: '{name}'.")
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
        links: Optional[Mapping[str, Union[str, Mapping[str, Any]]]] = None,
        relationships: Optional[Dict] = None,
        dontformat: bool = False
    ) -> Dict:
        """Export the object as a dictionary in compliance with JSON:API specification.

        ###### Parameters ######

        - `required_attributes`: an iterable containing the fields names to
        include in dumped data. If all fields are required, provide the
        `"__all__"` literal instead of an iterable.
        - `links`: a dictionary containing links payload to include in data.
        The keys are the links names to dump, and the values are dictionaries
        containing keyword arguments to pass to the factory function. Raw strings
        can also be provided for unregistered links names.
        - `relationships`: a dictionary specifying the relationships to include,
        if the identifier object must be exported, and which links must be dumped.
        The keys must be the relationships names and the value of each key is
        another dict containing two keys:
          + `"data"`: a boolean indicating if an identifier object must be included.
            If there is identifier meta attributes, they are also exported.
          + `"links"`: a dictionary in the same shape as the `links` argument.
        - `dontformat`: if `True`, do not format automatically fields names to
          camelCase. Default: `False`.

        ###### Returned value ######

        A dictionary representing the object in compliance with the JSON:API
        specification.

        ###### Errors raised ######

        A `ValueError` is raised if:
        - An attribute name in `required_attributes` argument is invalid.
        - A link name in `links` argument is not registered.
        - A key of the `relationship` argument does not refer to a valid
        related resource.
        - A link name of a specified relationship is not registered.

        ###### Examples ######

        Given

        ```python
        aresource = AResource(id=1)
        bresource = BResource(id=1, name="foo", related=aresource)
        ```

        A classic dump of `bresource` would be:

        ```python
        bresource.jsonapi_dict(
            required_attributes="__all__",
            links={"self": {"x": bresource.id}},
            relationships={
                "related":{
                    "data": True,
                    "links": {"self": {"x": bresource.id}}}})

        # {'type': 'BResource',
        #  'id': 1,
        #  'attributes': {'name': 'foo'},
        #  'relationships': {'related':
        #    {'links': {'self': '/b/1/relationships/related'},
        #     'data': {'type': 'AResource', 'id': 1}}},
        #  'links': {'self': '/b/1'}}
        ```

        An export example with a raw string link:

        ```python
        aresource.jsonapi_dict(
            "__all__",
            {"self": f"/a/{aresource.id}"})

        # {'type': 'AResource', 'id': 1, 'links': {'self': '/a/1'}}
        ```

        """
        if not hasattr(self, "id"):
            raise AttributeError(f"This '{self.__class__.__name__}' object has no id.")
        data = {
            "type": self.__resource_name__,
            "id": self.id,
        }
        filtered_attributes, meta_attributes = self._filtered_attributes(
            required_attributes, dontformat)
        if filtered_attributes:
            data["attributes"] = filtered_attributes
        if relationships:
            self._validate_relationships(relationships)
            data["relationships"] = self._formatted_relationships(relationships)
        if links:
            self._validate_links(links)
            data["links"] = self._make_links(links)
        if meta_attributes:
            data["meta"] = meta_attributes
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
    def register_link_factory(cls, name: str, factory: Callable[..., str]):
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
        _validate_link_name(cls, name)
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
        if self.__identifier_meta_attributes__:
            identifier_dict["meta"] = {name: getattr(self, name) for name in self.__identifier_meta_attributes__}
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

        Check if the passed names are keys of the __links_factories__ special
        attribute. If not, see if the links argument is a dictionary and try
        to get the value of the keys not present in __links_factories__.
        If at least one name is not valid, raise a `ValueError`.
        """
        errors = []
        for name in links:
            qual_name = cls._qualname(name, relationship)
            if qual_name in cls.__links_factories__:
                if not isinstance(links[name], Mapping):
                    errors.append(f"    You must provide an arguments dictionary for '{qual_name}' link.")
                continue
            provided_link = links.get(name)
            if provided_link is None:
                errors.append(f"    Nothing provided for building '{qual_name}' link.")
            elif not isinstance(links[name], str):
                errors.append(f"    Provided '{qual_name}' link is not a string.")
        if errors:
            raise ValueError("\n" + "\n".join(errors))

    ###########################################################################
    #            F O R M A T T I N G   A N D   F I L T E R I N G              #
    ###########################################################################

    def _filtered_attributes(
        self, required_attributes: Union[Iterable, Literal["__all__"]], dontformat=False
    ) -> Tuple[Dict, Dict]:
        """Filter the attributes with provided `required_attributes` iterable.

        If a member of the iterable is not in the annotated attributes, raise a
        `ValueError`. The names are converted from snake case to camel case.
        """
        if required_attributes == "__all__":
            required_attributes = self.__atomic_fields_set__ | {"meta"}
        required_attributes = set(required_attributes)
        errors = []
        attrs = {name: getattr(self, name, None) for name in required_attributes-{"meta"}}
        for name in required_attributes - {"meta"}:
            if name not in self.__atomic_fields_set__:
                errors.append(f"    Unexpected required attribute: '{name}'.")
                continue
            if attrs.get(name) is None:
                if not utils.is_an_optional_type_hint(self.__fields_types__[name]):
                    errors.append(f"    Missing required attribute: '{name}'.")
        if errors:
            raise ValueError("\n" + "\n".join(errors))
        attrs = {
            utils.snake_to_camel_case(k, dontformat): v
            for (k, v) in attrs.items()
            if k in set(required_attributes) - self._identifier_fields
        }
        meta_attrs = {
            utils.snake_to_camel_case(name, dontformat): getattr(self, name)
            for name in self.__meta_attributes__
            if getattr(self, name) is not None
        } if "meta" in required_attributes else None
        return attrs, meta_attrs

    def _formatted_relationships(self, relationships: Dict) -> Dict:
        """Format relationships into the JSON:API format."""
        relationships_dict = {}
        for name, rel_payload in relationships.items():
            rel_value: Union[Iterable[BaseResource], BaseResource] = self.__dict__[name]
            multiple_relationship = isinstance(rel_value, collections.abc.Iterable)
            if not rel_value:  # None or empty
                relationships_dict[name] = [] if multiple_relationship else None
                continue
            relationship_links = rel_payload.get("links")
            data_is_required = rel_payload.get("data")
            rel_data = {}
            if relationship_links:
                self._validate_links(relationship_links, relationship=name)
                rel_data["links"] = self._make_links(relationship_links, relationship=name)
            relationships_dict[name] = rel_data
            if data_is_required:
                rel_data["data"] = (
                    [rel._identifier_dict for rel in rel_value]
                    if multiple_relationship
                    else rel_value._identifier_dict
                )
        return relationships_dict

    def _make_links(self,
                    links: Mapping[str, Union[str, Dict[str, Any]]],
                    relationship: Optional[str] = None):
        """Build and return the links dictionary.

        The links are assumed to be valid. See _validate_links() for validation
        """
        evaluated_links = copy.deepcopy(links)
        for name, link in links.items():
            for param in link:
                if callable(link[param]):
                    evaluated_links[name][param] = link[param](self)
        return {
            name: self.__links_factories__[self._qualname(name, relationship)](**evaluated_links[name])
            if self.__links_factories__.get(self._qualname(name, relationship)) is not None
            else evaluated_links[name]
            for name in evaluated_links
        }

    ###########################################################################
    #                     S P E C I A L   M E T H O D S                       #
    ###########################################################################

    def __repr__(self):
        return (f"{self.__class__.__name__}"
                f"({', '.join(f'{k}={repr(v)}' for k, v in self.__dict__.items())})")

    def __getattr__(self, name):
        """Dynamically return None or [] for not-yet-initialized fields"""
        if name == "id":
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        type_hint = self.__fields_types__.get(name)
        if type_hint is None:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        if utils.is_an_iterable_type_hint(type_hint):
            return []
        return None


def create_resource(
    name: str,
    meta_conf: Optional[Dict[str, Any]] = None,
    bases: Union[type, Tuple[type]] = BaseResource,
    metaklass: type = BaseResourceMeta,
    /,
    **fields_types
) -> Any:
    """Create dynamically a new resource class.

    ###### Parameters ######

    Positional:

    * `name`: The resource class name.
    * `meta_conf`: A dictionary containg configuration attributes (of the
      `Meta` inner class).
    * `bases`: A tuple containing parent classes. It must contain include
      `BaseResource`.
    * `metaklass`: The metaclass used to create the resource class (must
      be a subclass of `BaseResourceMeta`).

    Keywords:

    * `**fields_types`: The types of the fields as keyword arguments.

    ###### Returned value ######

    A new resource class.

    ###### Errors raised ######

    A `TypeError` is raised if `metaklass` is not a subclass of `BaseResourceMeta`.
    A `ValueError` is raised if `BaseResource` is not in `bases` argument.
    """
    if not issubclass(metaklass, BaseResourceMeta):
        raise TypeError(
            "Only a submetaclass of BaseResourceMeta can create a new "
            f"resource class. ('{metaklass}' provided.)")
    if isinstance(bases, type):
        bases = tuple(bases.mro())
    if BaseResource not in bases:
        raise TypeError(
            "'BaseResource' class must be a parent class of any resource "
            f"class. ('{bases}' provided.)")

    meta_inncer_class = type("Meta", (), meta_conf or {})
    namespace = {"__annotations__": fields_types, "Meta": meta_inncer_class}
    return metaklass(name, bases, namespace)
