from django.core.management.base import BaseCommand, CommandError
from matcher.models import BookCover


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):

        for cover in BookCover.objects.filter(image="").exclude(image_url=""):
            print(cover, cover.book, cover.book.pk)
            cover.download_image()
