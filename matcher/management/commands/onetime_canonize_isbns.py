from django.core.management.base import BaseCommand, CommandError
from matcher.models import Book


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):

        qs = Book.objects.exclude(isbn="")
        total = qs.count()
        counter = 0
        for book in qs:
            book.save()
            counter += 1
            if counter % 1000 == 0:
                print(f"{counter} of {total}")
