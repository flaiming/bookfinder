import pytest
from matcher.parsers import parse_price


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ("", None),
        ("asd", None),
        (123, 123),
        (123.3, 123.3),
        ("123", 123),
        ("CZK 309,00", 309),
        ("356.00 CZK", 356),
        ("12 CZK", 12),
    ],
)
def test_parse_price(test_input, expected):
    assert parse_price(test_input) == expected
