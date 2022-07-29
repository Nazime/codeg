import codegenerator
from codegenerator import Attribute


# SIMPLE INSTRUCTIONS #
def test_script_generation_simple_instruction():
    cg = codegenerator.line("x = 2")
    assert cg.generate_code() == "x = 2\n"


def test_script_generation_multiple_simple_instructions():
    script_builder = codegenerator.line("x = 2").line("y = x")
    assert script_builder.generate_code() == "x = 2\ny = x\n"


# BLOCKS #
def test_script_generation_simple_block():
    cg = codegenerator.block("if x").line("x += 1")
    assert cg.generate_code() == "if x:\n    x += 1\n"


def test_script_generation_nested_blocks():
    block1 = codegenerator.block("if x").line("x += 1")
    block1.block("if y").line("y += 1")
    assert (
        block1.generate_code()
        == """if x:
    x += 1
    if y:
        y += 1
"""
    )


# ======= #
# CLASSES #
# ======= #
def test_script_generation_empty_cls():
    cg = codegenerator.cls("A")
    assert cg.generate_code() == "class A:\n    pass\n"


def test_script_generation_empty_decorated_empty_cls():
    cg = codegenerator.cls("A").decorator("attr.s")
    assert cg.generate_code() == "@attr.s\nclass A:\n    pass\n"


def test_script_generation_empty_decorated_cls():
    cg = codegenerator.cls("A").decorator("attr.s").line("name = attr.ib()")
    assert cg.generate_code() == "@attr.s\nclass A:\n    name = attr.ib()\n"


# ========= #
# FUNCTIONS #
# ========= #


def test_simple_function():
    cg = codegenerator.function("f")
    assert cg.generate_code() == "def f():\n    pass\n"


def test_function_with_arguments():
    cg = codegenerator.function("f", [Attribute("x")])
    assert cg.generate_code() == "def f(x):\n    pass\n"

    cg = codegenerator.function("f", [Attribute("x", annotation=str)])
    assert cg.generate_code() == "def f(x: str):\n    pass\n"

    cg = codegenerator.function(
        "f", [Attribute("x", annotation=str), Attribute("y", kw_only=True)]
    )
    assert cg.generate_code() == "def f(x: str, *, y):\n    pass\n"


def test_simple_function_with_decorator():
    cg = codegenerator.function("f").decorator("decorate")
    assert cg.generate_code() == "@decorate\ndef f():\n    pass\n"


def test_simple_method():
    cg = codegenerator.method("f")
    assert cg.generate_code() == "def f(self):\n    pass\n"


def test_add_comment():
    cg = codegenerator.comment("bof")
    assert cg.generate_code() == "# bof\n"

    cg = codegenerator.comment("bof").comment("lol")
    assert cg.generate_code() == "# bof\n# lol\n"
