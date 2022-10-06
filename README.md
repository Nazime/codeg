[![Pypi version](https://img.shields.io/pypi/v/codeg.svg)](https://pypi.org/project/codeg/) [![Python versions](https://img.shields.io/pypi/pyversions/codeg.svg)](https://pypi.org/project/codeg/) [![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

-----------------

# codeg

Codeg (code generator) is a python library that allows you to generate python code dynamically.

**This library is still a work in progress**

## Quickstart

Let's say you want to generate the following class dynamically

```python
class Animal:
    def __init__(name: str):
        self.name = name
```



You can use the following code

```python
import codeg

code_cls = codeg.cls("Animal")
code__init = code_cls.method(
    "__init__", attributes=[codeg.Attribute("name", annotation=str)]
)
code__init.line("self.name = name")

code_cls.print()  # print the generated code

Animal = code_cls.build()  # eval the code and get it on a variable
animal = Animal("rex")
```
