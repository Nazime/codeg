import codeg
from codeg import Attribute


# TODO: rework function signatures
def test_build_script_function_signature():
    script = codeg.generate_function_signature([Attribute("x")])
    assert script == "x"

    script = codeg.generate_function_signature([Attribute("x"), Attribute("y")])
    assert script == "x, y"

    script = codeg.generate_function_signature(
        [Attribute("x"), Attribute("y"), Attribute("z")]
    )
    assert script == "x, y, z"


def test_build_script_function_signature_with_annotations():
    script = codeg.generate_function_signature([Attribute("x", annotation=int)])
    assert script == "x: int"

    script = codeg.generate_function_signature(
        [Attribute("x", annotation=int), Attribute("something", annotation=str)]
    )
    assert script == "x: int, something: str"


def test_build_script_function_signature_with_default_value():
    script = codeg.generate_function_signature([Attribute("x", default=10)])
    assert script == "x=10"

    script = codeg.generate_function_signature(
        [Attribute("x"), Attribute("y", default=10)]
    )
    assert script == "x, y=10"


def test_build_script_function_signature_with_default_value_and_annotations():
    script = codeg.generate_function_signature(
        [Attribute("x", default=10, annotation=int)]
    )
    assert script == "x: int = 10"

    script = codeg.generate_function_signature(
        [
            Attribute("x"),
            Attribute("y", default=10, annotation=int),
            Attribute("something", default="hey"),
        ]
    )
    assert script == "x, y: int = 10, something='hey'"


def test_build_script_function_signature_with_default_as_str():
    script = codeg.generate_function_signature([Attribute("x", default="hey")])
    assert script == "x='hey'"


def test_build_script_function_signature_add_self():
    script = codeg.generate_function_signature([Attribute("x")], add_self=True)
    assert script == "self, x"

    script = codeg.generate_function_signature(add_self=True)
    assert script == "self"


def test_build_script_function_signature_no_attributes():
    script = codeg.generate_function_signature()
    assert script == ""


def test_build_script_function_signature_kw_only():
    script = codeg.generate_function_signature(
        [Attribute("x"), Attribute("y", kw_only=True)]
    )
    assert script == "x, *, y"
