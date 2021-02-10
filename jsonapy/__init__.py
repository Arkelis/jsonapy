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

The `Meta` inner class is used to set the resource name (the `"type"` field).
Instances of this resource can be now dumped into JSON:API-structured
dictionaries:

```pycon
>>> guido = PersonResource(id=1, first_name="Guido", last_name="Van Rossum")
>>> guido.jsonapi_dict(required_attributes="__all__")
{'type': 'person',
 'id': 1,
 'attributes': {'firstName': 'Guido', 'lastName': 'Van Rossum'}}
```

It is also possible to specify the fields to dump in the dictionary.

```pycon
>>> guido.jsonapi_dict(required_attributes=["first_name"])
{'type': 'person',
 'id': 1,
 'attributes': {'firstName': 'Guido'}}
```

Instead of a dictionary, the `dump()` method allows to get a JSON string:

```pycon
>>> guido.dump(required_attributes=["first_name"])
'{"type": "person", "id": 1, "attributes": {"firstName": "Guido"}}'
```

## Links

Resource links can be specified by registering factory functions that will be
used to generate them using `register_link_factory()` method:

```pycon
>>> PersonResource.register_link_factory("self", lambda id_: f"http://my.api/persons/{id_})
```

Now, the `"self"` link can be used when exporting the object as a dictionary:

```pycon
>>> guido.jsonapi_dict(
...     links={"self"},
...     required_attributes="__all__",
... )
...
{
  'type': 'person',
  'id': 1,
  'attributes': {
    'firstName': 'Guido',
    'lastName': 'Van Rossum'
  },
  'links': {'self': 'http://my.api/persons/1'}
}
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

ArticleResource.register_link_factory(
    "self",
    lambda x: f"http://my.api/articles/{x}"
)
```

Specify the links for the relationships by prefixing the links name with the
name of the relationship:

```python
ArticleResource.register_link_factory(
    "author__related",
    lambda x: f"http://my.api/articles/{x}/author"
)

```

Then, when you export an article, you can indicate the relationships you want
to dump by passing a dictionary to the `relationships` parameter.

```pycon

>>> zola = PersonResource(id=1, first_name="Emile", last_name="Zola")
>>> jaccuse = ArticleResource(id=1, title="J'accuse… !", author=zola)
>>> jaccuse.jsonapi_dict(
...     required_attributes="__all__",
...     links={"self"},
...     relationships={"author": {"data": True, "links": {"related"}}
... )
...
{
  'type': 'article',
  'id': 1,
  'attributes': {'title': "J'accuse… !"},
  'links': {'self': 'http://my.api/articles/1'},
  'relationships': {
    'author': {
      'data': {'type': 'person', 'id': 1},
      'links': {'related': 'http://my.api/articles/1/author'}
    }
  }
}
```


## Complete reference

For a more complete reference about resources, see `jsonapy.base` module.

"""


__version__ = "0.1.1"

from .base import BaseResource
