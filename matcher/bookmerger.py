import logging
from django.db import transaction
from matcher.models import Book, BookProfile, BookCover, BookPrice, BookPriceType
from matcher.utils import clean_isbn

logger = logging.getLogger(__name__)


def match_subname(name1, name2):
    name1 = name1.lower().strip()
    name2 = name2.lower().strip()
    if not name1 or not name2:
        return False
    # Full match or one of names is contained in other
    return name1 == name2 or name1 in name2 or name2 in name1


class BookMerger:
    CREATED = 1
    UPDATED = 2

    @classmethod
    def create_if_not_exists(cls, item):
        """
        Item = {
            "name",
            "isbn",
            "pages",
            "year",
            "issue",
            "cover",
            "profile_url",
            "prices": [
                {
                    "id",
                    "price",
                    "price_type"
                {
            ],
        }
        """

        def get_data(field, default=""):
            res = item.get(field, default)
            if res:
                if isinstance(res, str):
                    res = res.strip()
                return res
            return default

        deny_merge_on_fields = get_data("deny_merge_on_fields", [])
        name = get_data("name")
        isbn = clean_isbn(get_data("isbn"))
        pages = get_data("pages")
        try:
            pages = int(pages)
        except (TypeError, ValueError):
            pages = 0
        language = get_data("language")
        year = get_data("year")
        try:
            year = int(year)
        except (TypeError, ValueError):
            year = None
        issue = get_data("issue")
        # TODO save issue
        cover = get_data("cover")
        profile_url = get_data("profile_url")
        prices = get_data("prices", [])
        author = get_data("author")

        result_status = None
        books = cls.find_existing_books(profile_url, name, isbn, year, deny_merge_on_fields=deny_merge_on_fields)
        if books:
            # update book
            book = books[0]
            result_status = cls.UPDATED
            if book.name.lower() != name.lower():
                book.other_names.append(name)
            if isbn:
                book.isbn = isbn
            if language:
                book.language = language
            if pages:
                book.pages = pages
            if year:
                book.year = year

            book.save()
            # TODO update author

        else:
            result_status = cls.CREATED
            # create new book
            book = Book.objects.create(
                name=name,
                isbn=isbn,
                language=language,
                pages=pages,
                year=year,
            )
            # TODO create author

        # TODO better handle book with no profile_url

        if profile_url:
            profile = BookProfile.objects.get_or_create(url=profile_url)[0]
            profile.books.add(book)

            if cover:
                BookCover.objects.update_or_create(book=book, image_url=cover, defaults=dict(profile=profile))

            for price in prices:
                BookPrice.objects.update_or_create(
                    orig_id=price["id"],
                    profile=profile,
                    book=book,
                    defaults={
                        "price": price["price"],
                        "price_type": price["price_type"]
                    }
                )

        return book, result_status

    @staticmethod
    def find_existing_books(profile_url="", name="", isbn="", year=None, deny_merge_on_fields=None):
        assert profile_url or (name and (isbn or year)), "find_existing_book should have at least one parameter filled"

        deny_merge_on_fields = deny_merge_on_fields or []

        books = []
        # find by profile URL first
        if profile_url and "profile_url" not in deny_merge_on_fields:
            profile = BookProfile.objects.filter(url=profile_url).first()
            if profile:
                books = list(profile.books.all())
                if len(books) == 1:
                    logger.info(f"bookmerger: Merging by profile_url: {profile_url}")
                    return [books[0]]
                elif isbn:
                    # TODO tests!!!
                    # find book by matching ISBN
                    for book in books:
                        if book.isbn == isbn:
                            logger.info(f"bookmerger: Merging by profile_url AND matching ISBN: {isbn}, {profile_url}")
                            return [book]

        if not books:
            if isbn:
                # try find book by ISBN
                books = list(Book.objects.filter(isbn=isbn).order_by("created"))
            elif name and year:
                # try name with year
                books = list(Book.objects.filter(year=year, name__iexact=name).order_by("created"))

        if len(books) == 1:
            if match_subname(books[0].name, name):
                logger.info(f"bookmerger: Merging by isbn/name+year (only 1 found): {isbn}, {name}, {year}")
                return [books[0]]
        elif len(books) > 1:
            results = []
            for book in books:
                if match_subname(book.name, name):
                    results.append(book)
            logger.info(f"bookmerger: Merging by isbn/name+year ({len(results)} found): {isbn}, {name}, {year}")
            return results
        return None

    @classmethod
    def merge_book(cls, book, book_to_merge):
        # simple fields
        # TODO merge name? isbn? language? year?
        # TODO merge some fields by source priority

        with transaction.atomic():
            if not book.isbn:
                book.isbn = book_to_merge.isbn
            if not book.year:
                book.year = book_to_merge.year
            if not book.pages:
                book.pages = book_to_merge.pages
            elif book_to_merge.pages and book_to_merge.pages != book.pages:
                book.pages = max(book_to_merge.pages, book.pages)

            # TODO merge author

            # merge names
            if book_to_merge.name.lower() != book.name.lower():
                other_names = set([name.lower() for name in book.other_names])
                if book_to_merge.name.lower() not in other_names:
                    book.other_names.append(book_to_merge.name)

            # merge related objects
            for model in (BookCover, BookPrice):
                model.objects.filter(book=book_to_merge).update(book=book)

            book.profiles.add(*book_to_merge.profiles.all())

            book.save()
            book_to_merge.delete()
        return book
