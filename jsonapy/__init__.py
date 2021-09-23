# Copyright (c) 2021 Guillaume Fayard
# This library is licensed under the MIT license
# For a complete copy of the license, see the LICENSE file.

""" # JSON:APy - Dumping JSON:API in Python

> **WIP:** this library is still in early development phase.

`jsonapy` is a Python library for dumping models into
[JSON:API-compliant](https://jsonapi.org/) JSON.

This library is provided under the [MIT License](https://pycolore.mit-license.org),
its source is hosted on [GitHub](https://github.com/Arkelis/jsonapy).

## Basics

This package lets you define models and dump them into dictionaries with the
JSON:API structure. First, define a resource, it is a class inheriting from
`jsonapy.base.BaseResource` in which the fields are defined with annotations:

```python
import jsonapy

class PersonResource(jsonapy.BaseResource):
    id: int
    first_name: str
    last_name: str

    class Meta:
        resource_name = "person"
```

The `Meta` inner class is used to set some fields-typing-unrelated configuration,
like the the resource name (the `"type"` field). Instances of this resource
can be now dumped into JSON:API-structured dictionaries:

```python
guido = PersonResource(id=1, first_name="Guido", last_name="Van Rossum")
guido.jsonapi_dict(required_attributes="__all__")

# {'type': 'person',
#  'id': 1,
#  'attributes': {'firstName': 'Guido', 'lastName': 'Van Rossum'}}
```

It is also possible to specify the fields to dump in the dictionary.

```python
guido.jsonapi_dict(required_attributes=["first_name"])

# {'type': 'person',
#  'id': 1,
#  'attributes': {'firstName': 'Guido'}}
```

Instead of a dictionary, the `dump()` method allows to get a JSON string:

```python
guido.dump(required_attributes=["first_name"])

# '{"type": "person", "id": 1, "attributes": {"firstName": "Guido"}}'
```

## Links

Resource links can be specified by registering factories functions that will
be used to generate them using the `register_link_factory()` method:

```python
PersonResource.register_link_factory("self", lambda x: f"http://my.api/persons/{x})
```

Now, the `"self"` link can be used when exporting the object as a dictionary:

```python
guido.jsonapi_dict(
    links={"self": {"x": guido.id}},
    required_attributes="__all__")

# {
#   'type': 'person',
#   'id': 1,
#   'attributes': {
#     'firstName': 'Guido',
#     'lastName': 'Van Rossum'
#   },
#   'links': {'self': 'http://my.api/persons/1'}
# }
```

Links can also be added at dumping time without being registered by providing
a raw string.

```python
guido.jsonapi_dict(
    links={
        "self": {"x": guido.id},
        "languages": "http://my.api/persons/1/languages"},
    required_attributes="__all__")

# {
#   'type': 'person',
#   'id': 1,
#   'attributes': {
#     'firstName': 'Guido',
#     'lastName': 'Van Rossum'
#   },
#   'links': {
#     'self': 'http://my.api/persons/1'
#     'languages': 'http://my.api/persons/1/languages'
#   }
# }
```

## Relationships

You can create related models:

```python
class ArticleResource(jsonapy.BaseResource):
    id: int
    title: str
    author: PersonResource

    class Meta:
        resource_name = "article"
        # links factories can also be specified in Meta:
        links_factories = {
            "self": lambda x: f"http://my.api/articles/{x}",
            # for relationships, prefix the relationship name
            "author__related": lambda x: f"http://my.api/articles/{x}/author"}
```

Then, when you export an article, you can indicate the relationships you want
to dump by passing a dictionary to the `relationships` parameter.

```python
zola = PersonResource(id=1, first_name="Emile", last_name="Zola")
jaccuse = ArticleResource(id=1, title="J'accuse… !", author=zola)
jaccuse.jsonapi_dict(
    required_attributes="__all__",
    links={"self": {"x": jaccuse.id}},
    relationships={
        "author": {
            "data": True,
            "links": {"related": {"x": jaccuse.id}}}
)

# {
#   'type': 'article',
#   'id': 1,
#   'attributes': {'title': "J'accuse… !"},
#   'links': {'self': 'http://my.api/articles/1'},
#   'relationships': {
#     'author': {
#       'data': {'type': 'person', 'id': 1},
#       'links': {'related': 'http://my.api/articles/1/author'}
#     }
#   }
# }

```

## Accessing metadata about resources

The `jsonapy.functions` module provide top level functions for accessing some
information about resource classes.

## Reference of resource definition

For a more complete reference about resources, see `jsonapy.base` module.
"""


from .base import BaseResource
from .functions import fields_types
from .functions import relationships_names
from .functions import attributes_names
