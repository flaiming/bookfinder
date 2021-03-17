import os
from PIL import Image
import imagehash

from django.core.management.base import BaseCommand
from matcher.models import BookCover


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):

        example_image_path = os.path.join("bohaty_orez.jpg")

        example_hash = imagehash.dhash(Image.open(example_image_path))
        print(example_hash)

        for cover in BookCover.objects.exclude(image="")[:10]:
            print(cover, cover.book, cover.book.pk)
            img_hash = imagehash.dhash(Image.open(cover.image.path))
            print(img_hash)
            print(example_hash - img_hash)

