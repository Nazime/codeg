import codeg
import pytest


def test_simple_if():
    cg = codeg.if_("age > 18")
    assert (
        cg.generate_code()
        == """if age > 18:
    pass
"""
    )


def test_if_else():
    cg = codeg.if_("age > 18")
    cg.else_()
    assert (
        cg.generate_code()
        == """if age > 18:
    pass
else:
    pass
"""
    )


def test_if_elif():
    cg = codeg.if_("age > 18")
    cg.elif_("age > 15")
    assert (
        cg.generate_code()
        == """if age > 18:
    pass
elif age > 15:
    pass
"""
    )


def test_if_elif_elif():
    cg = codeg.if_("age > 18")
    cg.elif_("age > 15")
    cg.elif_("age > 10")
    assert (
        cg.generate_code()
        == """if age > 18:
    pass
elif age > 15:
    pass
elif age > 10:
    pass
"""
    )


def test_if_elif_elif_else():
    cg = codeg.if_("age > 18")
    cg.elif_("age > 15")
    cg.elif_("age > 10")
    cg.else_()
    assert (
        cg.generate_code()
        == """if age > 18:
    pass
elif age > 15:
    pass
elif age > 10:
    pass
else:
    pass
"""
    )


def test_if_elif_elif_else_complete():
    import codeg

    cg = codeg.if_("age > 18").line("print('18+')")
    cg.elif_("age > 15").line("print('15-18')")
    cg.elif_("age > 10").line("print('10-15')")
    cg.else_().line("print('10-')")
    cg.generate_code()
    assert (
        cg.generate_code()
        == """if age > 18:
    print("18+")
elif age > 15:
    print("15-18")
elif age > 10:
    print("10-15")
else:
    print("10-")
"""
    )


def test_condition_inside_block():
    cg = codeg.function("f")
    cg.if_("True")
    assert (
        cg.generate_code()
        == """def f():
    if True:
        pass
"""
    )


def test_error_multiple_else():
    cg = codeg.if_("True")
    cg.else_()

    with pytest.raises(codeg.CodegSyntaxError):
        cg.else_()


def test_error_elif_after_else():
    cg = codeg.if_("True")
    cg.else_()

    with pytest.raises(codeg.CodegSyntaxError):
        cg.elif_("True")


def test_error_attribute_error():
    with pytest.raises(AttributeError):
        codeg.else_

    with pytest.raises(AttributeError):
        codeg.elif_

    cg = codeg.function("f")
    with pytest.raises(AttributeError):
        cg.else_

    with pytest.raises(AttributeError):
        cg.elif_
