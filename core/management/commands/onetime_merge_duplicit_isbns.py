from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from .models import Book
from .bookmerger import BookMerger, match_subname


class Command(BaseCommand):
    help = ""

    def add_arguments(self, parser):
        parser.add_argument(
            "--save", action="store_true", default=False, help="Do not change data",
        )

    def handle(self, *args, **options):
        save = options["save"]

        qs = Book.objects.exclude(isbn="")
        total = qs.count()

        counter = 0
        #for book in qs[:100]:
        for isbn in qs.values("isbn").annotate(cnt=Count("isbn")).order_by("-cnt").filter(cnt__gt=1).values_list("isbn", flat=True):
            print()
            print(isbn)
            for book in Book.objects.filter(isbn=isbn):
                print(book)
                candidates = list(BookMerger.find_existing_books(name=book.name, isbn=book.isbn, year=book.year))
                if len(candidates) > 1:
                    base_book = candidates[0]
                    print("base book", base_book)
                    for candidate in candidates[1:]:
                        print("---", candidate)
                        if match_subname(candidate.name, base_book.name):
                            print(f"=================MERGE: {base_book} <-- {candidate}")
                            print(base_book.profiles.all())
                            print(candidate.profiles.all())
                            if save:
                                BookMerger.merge_book(base_book, candidate)

            counter += 1
            if counter % 100 == 0:
                print(f"{counter} of {total}")

