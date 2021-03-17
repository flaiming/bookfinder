from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from matcher.models import Book


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):

        qs = Book.objects.exclude(isbn="")
        total = qs.count()

        counter = 0
        for book in qs.values("isbn").annotate(cnt=Count("isbn")).order_by("-cnt").filter(cnt__gt=1):
            print()
            print(book)
            isbn = book["isbn"]
            # find candidates to merge
            books = qs.filter(isbn=isbn).order_by("created")

            # merge books
            for b in books:
                print(b)
                price = b.prices.first()
                if price:
                    print("=======", price.source)

            ##################
            # zatim neresit, dokud neprijdu na to jak si poradit s duplicitnimi ISBN

            counter += 1
            if counter % 1000 == 0:
                print(f"{counter} of {total}")

