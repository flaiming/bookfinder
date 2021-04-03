from django.db import transaction
from matcher.models import Book, BookProfile, BookCover, BookPrice, BookPriceType
from matcher.utils import clean_isbn


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
        deny_merge_on_fields = item.get("deny_merge_on_fields", [])
        name = item.get("name", "").strip()
        isbn = clean_isbn(item.get("isbn", "")).strip()
        pages = item.get("pages", "")
        try:
            pages = int(pages)
        except ValueError:
            pages = 0
        language = item.get("language", "").strip()
        year = item.get("year")
        try:
            year = int(year)
        except (TypeError, ValueError):
            year = None
        issue = item.get("issue", "").strip()
        # TODO save issue
        cover = item.get("cover", "").strip()
        profile_url = item.get("profile_url", "").strip()
        prices = item.get("prices", [])
        author = item.get("author", "").strip()

        result_status = None
        books = cls.find_existing_books(profile_url, name, isbn, year, deny_merge_on_fields=deny_merge_on_fields)
        if books:
            book = books[0]
            result_status = cls.UPDATED
            # update book
            book.name = name
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
        if "profile_url" not in deny_merge_on_fields:
            profile = BookProfile.objects.filter(url=profile_url).first()
            if profile:
                books = list(profile.books.all())
                if len(books) == 1:
                    return [books[0]]
                elif isbn:
                    # TODO tests!!!
                    # find book by matching ISBN
                    for book in books:
                        if book.isbn == isbn:
                            return [book]

        if not books:
            if isbn:
                # try find book by ISBN
                books = list(Book.objects.filter(isbn=isbn).order_by("created"))
            elif name and year:
                # try name with year
                books = list(Book.objects.filter(year=year, name__iexact=name).order_by("created"))

        if len(books) == 1:
            if books[0].name.lower() == name.lower():
                return [books[0]]
        elif len(books) > 1:
            results = []
            for book in books:
                if book.name.lower() == name.lower():
                    results.append(book)
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

            # TODO merge author

            # merge related objects
            for model in (BookProfile, BookCover, BookPrice):
                model.objects.filter(book=book_to_merge).update(book=book)

            book.save()
            book_to_merge.delete()
        return book
