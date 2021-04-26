import pytest

from matcher.models import Book, BookProfile, BookPrice, BookPriceType, BookCover
from matcher.bookmerger import BookMerger, match_subname


@pytest.fixture
def book_potter(db):
    book = Book.objects.create(name="Harry Potter", isbn="9788000011615", year=2000, language="en", pages=350)
    profile = BookProfile.objects.create(url="https://foo.bar/parry")
    profile.books.add(book)
    BookPrice.objects.create(price=1000, orig_id="123", price_type=BookPriceType.OFFER, book=book, profile=profile)
    yield book
    book.delete()

#### What to test?

# create new book
# update existing book


def test_create_book(db):
    data = {
        "name": "Parry Lotter",
        "isbn": "978-80-88362-00-5",
        "language": "cz",
        "pages": 100,
        "year": 2010,
        "profile_url": "https://foo.bar/parry",
    }
    book, status = BookMerger.create_if_not_exists(data)
    assert status == BookMerger.CREATED
    assert book.name == "Parry Lotter"
    assert book.isbn == "9788088362005"
    assert book.language == "cz"
    assert book.pages == 100
    assert book.year == 2010
    profiles = list(book.profiles.all())
    assert len(profiles) == 1
    assert profiles[0].url == "https://foo.bar/parry"


def test_update_book_by_profile_url(book_potter):
    data = {
        "name": "Parry Lotter",
        "isbn": "978-80-88362-00-5",
        "language": "cz",
        "pages": 100,
        "year": 2010,
        "profile_url": "https://foo.bar/parry",
    }
    book, status = BookMerger.create_if_not_exists(data)
    assert status == BookMerger.UPDATED
    assert book.name == "Harry Potter"
    assert book.isbn == "9788088362005"
    assert book.language == "cz"
    assert book.pages == 100
    assert book.year == 2010
    profiles = list(book.profiles.all())
    assert len(profiles) == 1
    assert profiles[0].url == "https://foo.bar/parry"
    assert Book.objects.count() == 1


def test_update_book_by_isbn_and_name(book_potter):
    data = {
        "name": "harry potter",
        "isbn": "9788000011615",
        "pages": 100,
        "year": 2010,
    }
    book, status = BookMerger.create_if_not_exists(data)
    assert status == BookMerger.UPDATED
    assert book.name == "Harry Potter"
    assert book.isbn == "9788000011615"
    assert book.pages == 100
    assert book.year == 2010
    assert Book.objects.count() == 1


def test_update_book_by_isbn_and_partial_name(book_potter):
    data = {
        "name": "harry potter and philosophers stone",
        "isbn": "9788000011615",
    }
    book, status = BookMerger.create_if_not_exists(data)
    assert status == BookMerger.UPDATED
    assert book.name == "Harry Potter"
    assert book.isbn == "9788000011615"
    assert book.pages == 350
    assert book.year == 2000
    assert Book.objects.count() == 1


def test_update_book_by_name_and_year(book_potter):
    data = {
        "name": "harry potter",
        "pages": 100,
        "year": 2000,
    }
    book, status = BookMerger.create_if_not_exists(data)
    assert status == BookMerger.UPDATED
    assert book.name == "Harry Potter"
    assert book.isbn == "9788000011615"
    assert book.pages == 100
    assert book.year == 2000
    assert Book.objects.count() == 1


def test_create_book_with_same_isbn_different_name(book_potter):
    data = {
        "name": "Parry Lotter",
        "isbn": "9788000011615",
        "pages": 100,
        "year": 2010,
    }
    book, status = BookMerger.create_if_not_exists(data)
    assert status == BookMerger.CREATED
    assert book.name == "Parry Lotter"
    assert book.isbn == "9788000011615"
    assert book.pages == 100
    assert book.year == 2010
    assert Book.objects.count() == 2


def test_create_book_with_same_name_and_different_year(book_potter):
    data = {
        "name": "harry potter",
        "pages": 100,
        "year": 2001,
    }
    book, status = BookMerger.create_if_not_exists(data)
    assert status == BookMerger.CREATED
    assert book.name == "harry potter"
    assert book.isbn == ""
    assert book.pages == 100
    assert book.year == 2001
    assert Book.objects.count() == 2


def test_update_book_prices_by_profile_url(book_potter):
    data = {
        "prices": [
            {
                "id": "123",
                "price": 2000,
                "price_type": BookPriceType.OFFER,
            }
        ],
        "profile_url": "https://foo.bar/parry",
    }
    book, status = BookMerger.create_if_not_exists(data)
    assert status == BookMerger.UPDATED
    assert Book.objects.count() == 1
    prices = list(book_potter.prices.all())
    assert len(prices) == 1
    assert prices[0].price == 2000
    assert prices[0].price_type == BookPriceType.OFFER


def test_create_book_prices_by_profile_url(book_potter):
    data = {
        "prices": [
            {
                "id": "1",
                "price": 2000,
                "price_type": BookPriceType.REQUEST,
            }
        ],
        "profile_url": "https://foo.bar/parry",
    }
    book, status = BookMerger.create_if_not_exists(data)
    assert status == BookMerger.UPDATED
    assert Book.objects.count() == 1
    prices = list(book_potter.prices.order_by("created"))
    assert len(prices) == 2
    assert prices[0].price == 1000
    assert prices[0].price_type == BookPriceType.OFFER
    assert prices[1].price == 2000
    assert prices[1].price_type == BookPriceType.REQUEST


def test_create_book_with_empty_profile_url(db):
    data = {
        "name": "Larry Page",
        "year": 2010,
        "profile_url": "",
    }
    book, status = BookMerger.create_if_not_exists(data)
    assert status == BookMerger.CREATED
    assert Book.objects.count() == 1
    assert book.prices.count() == 0
    assert book.profiles.count() == 0


@pytest.mark.parametrize(
    "name1, name2, expected",
    [
        ("", "", False),
        ("harry potter", "harry potter", True),
        ("Harry Potter", "harry potter", True),
        (" Harry Potter", "harry potter ", True),
        ("Harry Potter", "harry Potter and Philosopher stone", True),
        ("Harry Potter", "Harry Lotter", False),
        ("foo", "Harry Lotter", False),
        ("", "Harry Lotter", False),
    ],
)
def test_match_subname(name1, name2, expected):
    assert match_subname(name1, name2) is expected

