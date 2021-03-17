import os
from PIL import Image
import imagehash

from django.core.management.base import BaseCommand
from matcher.models import BookCover


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        qs = BookCover.objects.exclude(image="")

        if True:
            qs = qs.filter(hash_short="")

        print("count: ", qs.count())

        counter = 0
        for cover in qs:
            try:
                if not os.path.exists(cover.image.path):
                    cover.download_image()
                if not cover.book.pk:
                    print("No image, possible empty image")
                    continue
                with Image.open(cover.image.path) as img:
                    hash_short = imagehash.dhash(img, 16)
                    hash_long = imagehash.dhash(img, 32)
                    cover.hash_short = hash_short
                    cover.hash_long = hash_long
                    cover.save(update_fields=["hash_short", "hash_long"])
            except Exception as e:
                print("ERROR", e)
            counter += 1
            if counter % 1000 == 0:
                print(counter)
