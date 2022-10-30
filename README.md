[![Pypi version](https://img.shields.io/pypi/v/codeg.svg)](https://pypi.org/project/codeg/) [![Python versions](https://img.shields.io/pypi/pyversions/codeg.svg)](https://pypi.org/project/codeg/) [![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

-----------------

# codeg

Codeg (code generator) is a python library that allows you to generate python code dynamically.

**This library is still a work in progress**

# Demonstration

## Create simple class

Let's say you want to generate the following class dynamically

```python
class Animal:
    def __init__(self, name: str):
        self.name = name
```



You can use the following code

```python
import codeg

# Create the 'Animal' class
code_cls = codeg.cls("Animal")

# Add the init method
code__init = code_cls.method(
    "__init__", parameters=[codeg.param("name", annotation=str)]
)

# Add a simple instruction
code__init.line("self.name = name")

# Print the generated code
code_cls.print()

# Get the generated code in a variable
script = code_cls.generate_code()

# Eval the code and get it on a variable
Animal = code_cls.build()

# Create an instance of our dynamically generated cls
animal = Animal("rex")
print(animal)
```

## Generate script

It is possible to generate and execute a script

```python
def double(i):
    x = i * 2
    return x


for i in range(10):
    print(double(i))
```

Dynamically generate the script above

```python
import codeg

# Create a new empty script
code_script = codeg.script()

# Create the 'double' function
code_function = code_script.function("double", ["i"])
code_function.line("x = i * 2")
code_function.return_("x")

# Create the 'for' loop
code_forloop = code_script.for_("i", "range(10)")
code_forloop.line("print(double(i))")

# Execute the script
build_dict = code_script.build()

# Get the 'double' function
double = build_dict["double"]
```

It is possible to chain the methods in the same line, since the methods ``line`` and ``return`` will return the current object:

```python
# We can replace the generation of function with the following code
code_script.function("double", ["i"]).line("x = i * 2").return_("x")
```

By chaining the methods we can have the same script with less code:

```python
import codeg

# Create a new empty script
code_script = codeg.script()

# Create the 'double' function
code_script.function("double", ["i"]).line("x = i * 2").return_("x")
# Create the 'for' loop
code_script.for_("i", "range(10)").line("print(double(i))")

# Execute the script
build_dict = code_script.build()

# Get the 'double' function
double = build_dict["double"]
```
