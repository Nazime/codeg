import codeg


def test_building_simple_function():
    c = codeg.function("f").ret("5")
    f = c.build()
    assert f() == 5

    c = codeg.function("f", [codeg.param("x")]).ret("x")
    f = c.build()
    assert f(5) == 5
    assert f(1) == 1


def test_bound_to_instance():
    c = codeg.method("f", [codeg.param("x")]).ret("x*x")
    # creating the following function
    """def f(self,  x):
        return x*x
"""

    class A:
        pass

    a = A()
    c.bound_to_instance(a)
    assert a.f(5) == 25

    c.bound_to_instance(a, "ff")
    assert a.ff(5) == 25


# TODO: test cls build
