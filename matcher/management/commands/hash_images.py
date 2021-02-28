from PIL import Image
import imagehash

from django.core.management.base import BaseCommand
from matcher.models import BookCover


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):

        counter = 0
        for cover in BookCover.objects.exclude(image=""):
            img = Image.open(cover.image.path)
            hash_short = imagehash.dhash(img, 16)
            hash_long = imagehash.dhash(img, 32)
            cover.hash_short = hash_short
            cover.hash_long = hash_long
            cover.save()

            img.close()
            counter += 1
            if counter % 1000 == 0:
                print(counter)
