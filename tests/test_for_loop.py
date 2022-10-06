import codeg
import pytest


def test_simple_for():
    cg = codeg.for_("i", "l")
    assert (
        cg.generate_code()
        == """for i in l:
    pass
"""
    )


def test_for_else():
    cg = codeg.for_("i", "l")
    cg.else_()
    assert (
        cg.generate_code()
        == """for i in l:
    pass
else:
    pass
"""
    )


def test_inside_block():
    cg = codeg.function("f")
    cg.for_("i", "l")
    assert (
        cg.generate_code()
        == """def f():
    for i in l:
        pass
"""
    )


def test_error_multiple_else():
    cg = codeg.for_("i", "l")
    cg.else_()

    with pytest.raises(codeg.CodegSyntaxError):
        cg.else_()


def test_error_attribute_error():
    cg = codeg.for_
    with pytest.raises(AttributeError):
        cg.elif_
