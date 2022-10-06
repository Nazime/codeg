import codeg
import pytest


def test_simple_try_except():
    cg = codeg.try_()
    cg.except_()
    assert (
        cg.generate_code()
        == """try:
    pass
except:
    pass
"""
    )


def test_simple_try_except_with_type():
    cg = codeg.try_()
    cg.except_("ValueError")
    assert (
        cg.generate_code()
        == """try:
    pass
except ValueError:
    pass
"""
    )


def test_simple_try_except_with_type_and_name():
    cg = codeg.try_()
    cg.except_("ValueError", "e")
    assert (
        cg.generate_code()
        == """try:
    pass
except ValueError as e:
    pass
"""
    )


def test_try_except_else():
    cg = codeg.try_()
    cg.except_()
    cg.else_()
    assert (
        cg.generate_code()
        == """try:
    pass
except:
    pass
else:
    pass
"""
    )


def test_many_except():
    cg = codeg.try_()
    cg.except_("ValueError")
    cg.except_("TypeError")
    assert (
        cg.generate_code()
        == """try:
    pass
except ValueError:
    pass
except TypeError:
    pass
"""
    )


def test_finally():
    cg = codeg.try_()
    cg.finally_()
    assert (
        cg.generate_code()
        == """try:
    pass
finally:
    pass
"""
    )


def test_complete_example():
    cg = codeg.try_()
    cg.except_("ValueError", "e")
    cg.except_("TypeError")
    cg.except_("Exception", "var")
    cg.else_()
    cg.finally_()
    assert (
        cg.generate_code()
        == """try:
    pass
except ValueError as e:
    pass
except TypeError:
    pass
except Exception as var:
    pass
else:
    pass
finally:
    pass
"""
    )


def test_condition_inside_block():
    cg = codeg.function("f")
    cg_try = cg.try_()
    cg_try.except_()
    assert (
        cg.generate_code()
        == """def f():
    try:
        pass
    except:
        pass
"""
    )


def test_error_multiple_else():
    cg = codeg.try_()
    cg.else_()

    with pytest.raises(codeg.CodegSyntaxError):
        cg.else_()


def test_error_multiple_finally():
    cg = codeg.try_()
    cg.finally_()

    with pytest.raises(codeg.CodegSyntaxError):
        cg.finally_()


def test_error_else_before_except():
    cg = codeg.try_()
    cg.else_()

    with pytest.raises(codeg.CodegSyntaxError):
        cg.except_()


def test_error_finally_before_except_or_else_finally():
    cg = codeg.try_()
    cg.finally_()

    with pytest.raises(codeg.CodegSyntaxError):
        cg.else_()


def test_error_attribute_error():
    with pytest.raises(AttributeError):
        codeg.except_

    with pytest.raises(AttributeError):
        codeg.finally_

    cg = codeg.function("f")
    with pytest.raises(AttributeError):
        cg.except_

    with pytest.raises(AttributeError):
        cg.finally_


# TODO: test raise
