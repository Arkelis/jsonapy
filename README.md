# JSON:APy - Loading and Dumping JSON:API in Python

> **WIP:** this library is still in early development phase.

`jsonapy` is a Python library for dumping models into
[JSON:API-compliant]("https://jsonapi.org/") JSON.

[![PyPi](https://img.shields.io/pypi/v/jsonapy?label=PyPi)](https://pypi.org/project/jsonapy/)
[![Python Version](https://img.shields.io/pypi/pyversions/jsonapy?label=Python)](https://pypi.org/project/jsonapy/)
![Tests & coverage](https://github.com/Arkelis/jsonapy/workflows/Tests%20&%20coverage/badge.svg)
[![codecov](https://codecov.io/gh/Arkelis/jsonapy/branch/master/graph/badge.svg?token=ZRF5RAF8NG)](https://codecov.io/gh/Arkelis/jsonapy)

## Installation

With `pip`:

```
pip install jsonapy
```

## Basic usage overview

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

## [Documentation](https://arkelis.github.io/jsonapy/jsonapy.html)

The complete documentation can be found **[here](https://arkelis.github.io/jsonapy/jsonapy.html)**.
It is built with [pdoc]("https://github.com/mitmproxy/pdoc").

## [Roadmap](https://github.com/Arkelis/jsonapy/projects/1)

Refer to [the project](https://github.com/Arkelis/jsonapy/projects/1) to view the roadmap-related issues.
