from PIL import Image
import imagehash

from django.core.management.base import BaseCommand
from matcher.models import BookCover


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):

        # open searched image
        image_path = "_knihy/DSC02524.JPG"

        hash_short = imagehash.dhash(Image.open(image_path), 16)
        hash_long = imagehash.dhash(Image.open(image_path), 32)

        diffs_short = {}
        diffs_long = {}
        for cover in BookCover.objects.exclude(image=""):
            #print(cover.book)
            #print(cover.hash_short)
            #print(cover.image)
            cover_hash_short = imagehash.hex_to_hash(cover.hash_short)
            cover_hash_long = imagehash.hex_to_hash(cover.hash_long)
            #cover_hash_short = imagehash.dhash(Image.open(cover.image.path), 16)
            #cover_hash_long = imagehash.dhash(Image.open(cover.image.path), 32)
            diff_short = cover_hash_short - hash_short
            diff_long = cover_hash_long - hash_long
            print(diff_short)
            print(diff_long)

            diffs_short[cover.pk] = diff_short
            diffs_long[cover.pk] = diff_long

        short10 = sorted(diffs_short.items(), key=lambda x: x[1])[:10]
        long10 = sorted(diffs_long.items(), key=lambda x: x[1])[:10]
        print(short10)
        print(long10)
