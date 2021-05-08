from django.core.management.base import BaseCommand, CommandError
from .models import BookProfile


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):

        qs = BookProfile.objects.exclude(book=None).filter(books=None)
        total = qs.count()
        counter = 0
        for profile in qs:
            profile.books.add(profile.book)
            counter += 1
            if counter % 1000 == 0:
                print(f"{counter} of {total}")

