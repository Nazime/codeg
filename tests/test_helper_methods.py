import codeg
from codeg.codeg import normalize_parameters


def test_normalize_parameters():
    # Test None
    assert normalize_parameters(None) == []

    # Test str list
    assert normalize_parameters(["a"]) == [codeg.Parameter("a")]
    assert normalize_parameters(["a", "b", "c"]) == [
        codeg.Parameter("a"),
        codeg.Parameter("b"),
        codeg.Parameter("c"),
    ]

    # Test str Parameter
    assert normalize_parameters([codeg.Parameter("a", kw_only=True)]) == [
        codeg.Parameter("a", kw_only=True)
    ]

    # Test one str
    assert normalize_parameters("a") == [codeg.Parameter("a")]

    # Test one Parameter
    assert normalize_parameters(codeg.Parameter("a", kw_only=True)) == [
        codeg.Parameter("a", kw_only=True)
    ]

    # Test mixed str/Parameter list
    assert normalize_parameters(
        ["a", "b", "c", codeg.Parameter("d", kw_only=True)]
    ) == [
        codeg.Parameter("a"),
        codeg.Parameter("b"),
        codeg.Parameter("c"),
        codeg.Parameter("d", kw_only=True),
    ]
