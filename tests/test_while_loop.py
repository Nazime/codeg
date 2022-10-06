import codeg
import pytest


def test_simple_while():
    cg = codeg.while_("age > 18")
    assert (
        cg.generate_code()
        == """while age > 18:
    pass
"""
    )


def test_while_else():
    cg = codeg.while_("age > 18")
    cg.else_()
    assert (
        cg.generate_code()
        == """while age > 18:
    pass
else:
    pass
"""
    )


def test_while_inside_block():
    cg = codeg.function("f")
    cg.while_("True")
    assert (
        cg.generate_code()
        == """def f():
    while True:
        pass
"""
    )


def test_error_multiple_else():
    cg = codeg.while_("True")
    cg.else_()

    with pytest.raises(codeg.CodegSyntaxError):
        cg.else_()


def test_error_attribute_error():
    cg = codeg.while_
    with pytest.raises(AttributeError):
        cg.elif_
