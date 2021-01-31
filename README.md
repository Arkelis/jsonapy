# JSON:APy - Dumping JSON:API in Python

> **WIP:** this library is still in early development phase.

`jsonapy` is a Python library for dumping models into
[JSON:API-compliant]("https://jsonapi.org/") JSON.

## Basics

This package lets you define models and dump them into dict with the JSON:API
structure. First, define a resource:

```python
import jsonapy

class PersonResource(jsonapy.BaseResource):
    id: int
    first_name: str
    last_name: str

    class Meta:
        resource_name = "person"
```

You can now dump an instance of this resource into JSON:API-structured dictionary:

```python
guido = PersonResource(id=1, first_name="Guido", last_name="Van Rossum")
data = guido.jsonapi_dict(required_attributes="__all__")
```

The resulting `data` dictionary can be represented by:

```python
{
    'type': 'person',
    'id': 1,
    'attributes': {
        'firstName': 'Guido', 
        'lastName': 'Van Rossum'
    }
}
```
