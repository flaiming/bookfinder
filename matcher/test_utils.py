import pytest
from matcher.utils import clean_isbn, make_full_url


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ("", ""),
        ("foobar", ""),
        ("978-80-00-04151-3", "9788000041513"),
        ("978-80-00-04151", ""),  # without checksum number
        ("8085844818", "9788085844818"),
        ("9788073540835", "9788073540838"),  # wrongly prefixed "978" to isbn10
    ],
)
def test_clean_isbn(test_input, expected):
    assert clean_isbn(test_input) == expected


@pytest.mark.parametrize(
    "url, full_url",
    [
        ("/test", "https://seznam.cz/test"),
        ("/test", "https://seznam.cz/test"),
        ("?page=1", "https://seznam.cz/?page=1"),
        ("https://seznam.cz/index.php", "https://seznam.cz/index.php"),
    ],
)
def test_make_full_url(url, full_url):
    assert make_full_url("https://seznam.cz", url) == full_url
    assert make_full_url("https://seznam.cz/foo/bar/?testing=1", url) == full_url
