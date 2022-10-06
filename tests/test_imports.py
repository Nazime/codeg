import codeg


# TODO: test from
def test_simple_imports():
    cg = codeg.import_("math")

    assert (
        cg.generate_code()
        == """import math
"""
    )


def test_import_many_with_aliases():
    # import math as m, re, sys as s
    cg = codeg.import_(("math", "m"), "re", ("sys", "s"))

    assert (
        cg.generate_code()
        == """import math as m, re, sys as s
"""
    )
