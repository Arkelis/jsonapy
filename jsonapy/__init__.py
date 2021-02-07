# Copyright (c) 2021 Guillaume Fayard
# This library is licensed under the MIT license
# For a complete copy of the license, see the LICENSE file.

"""# JSON:APy - Dumping JSON:API in Python

> **WIP:** this library is still in early development phase.

`jsonapy` is a Python library for dumping models into
[JSON:API-compliant](https://jsonapi.org/) JSON.

This library is provided under the [MIT License](https://pycolore.mit-license.org),
its source is hosted on [GitHub](https://github.com/Arkelis/jsonapy).


## Basics

This package lets you define models and dump them into dict with the JSON:API
structure. First, define a resource, it is a class inheriting from
`jsonapy.base.BaseResource` in which the attributes are specified with annotations:

```python
import jsonapy

class PersonResource(jsonapy.BaseResource):
    id: int
    first_name: str
    last_name: str

    class Meta:
        resource_name = "person"
```

The `Meta` innerclass is used to set the resource name (the `"type"` field).
You can now dump an instance of this resource into JSON:API-structured dictionary:

```pycon
>>> guido = PersonResource(id=1, first_name="Guido", last_name="Van Rossum")
>>> guido.jsonapi_dict(required_attributes="__all__")
{'type': 'person',
 'id': 1,
 'attributes': {'firstName': 'Guido', 'lastName': 'Van Rossum'}}
```

You can also specify the attributes that you want to dump in the dictionary.

```pycon
>>> guido.jsonapi_dict(required_attributes=["first_name"])
{'type': 'person',
 'id': 1,
 'attributes': {'firstName': 'Guido'}}
```

Instead of a dictionary, the `dump()` method allows you to get a JSON string:

```pycon
>>> guido.dump(required_attributes=["first_name"])
'{"type": "person", "id": 1, "attributes": {"firstName": "Guido", "lastName": "Van Rossum"}}'
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
```

When you dump an article, you can specify the relationships you want to dump:

```pycon
>>> zola = PersonResource(id=1, first_name="Emile", last_name="Zola")
>>> jaccuse = ArticleResource(id=1, title="J'accuse… !", author=zola)
>>> jaccuse.jsonapi_dict(
...     required_attributes="__all__",
...     relationships={"author": {"data": True}}
... )
...
{'type': 'article',
 'id': 1,
 'attributes': {'title': "J'accuse… !"},
 'relationships': {'author': {'data': {'type': 'person', 'id': 1}}}}
```

## Links

You can specify the links of the resource by registering factory functions
that will be used to generate them.

```pycon
>>> jaccuse.jsonapi_dict(
...     links={"self": "http://my.api/articles/1"},
...     required_attributes="__all__",
...     relationships={"author": {
...     "data": True,
...     "links": {"self": "http://my.api/articles/1/author", "related": "http://my.api/authors/1"}
...     }}
... )
...
{
  "type": "article",
  "id": 1,
  "attributes": {
    "title": "J'accuse… !"
  },
  "links": {
    "self": "http://my.api/articles/1"
  },
  "relationships": {
    "author": {
      "data": {
        "type": "person",
        "id": 1
      },
      "links": {
        "self": "http://my.api/articles/1/author",
        "related": "http://my.api/authors/1"
      }
    }
  }
}
```

## Complete reference

For a more complete reference about resources, go to `jsonapy.base` module.

"""


__version__ = "0.1.1"

from .base import BaseResource
