from PIL import Image
import imagehash
import os
import csv

from django.core.management.base import BaseCommand
from django.db.models import Avg, Count
from matcher.models import BookCover, Book


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):

        # load images to search
        images = {}
        for image_name in os.listdir("_knihy"):
            image_path = os.path.join("_knihy", image_name)

            img = Image.open(image_path)
            hash_short = imagehash.dhash(img, 16)
            hash_long = imagehash.dhash(img, 32)
            images[image_path] = (hash_short, hash_long)

        diffs = {}
        for cover in BookCover.objects.exclude(image="").exclude(hash_short="").order_by("image").select_related("book"):
            print(cover.book)
            #print(cover.hash_short)
            #print(cover.image)
            cover_hash_short = imagehash.hex_to_hash(cover.hash_short)
            #cover_hash_long = imagehash.hex_to_hash(cover.hash_long)
            for image_path, hashes in images.items():
                diff_short = cover_hash_short - hashes[0]
                #diff_long = cover_hash_long - hashes[1]

                diffs.setdefault(image_path, {})
                diffs[image_path][cover.pk] = diff_short

                diffs[image_path] = dict(sorted(diffs[image_path].items(), key=lambda x: x[1])[:10])

        diffs = sorted(diffs.items(), key=lambda x: x[0])
        for image_path, diff in diffs:
            if diff:
                cover_id = list(diff.keys())[0]
                cover = BookCover.objects.get(pk=cover_id)
                print(f"{image_path} - {cover.book.name}")
                print(list(diff.values())[1] - list(diff.values())[0], BookCover.objects.get(pk=list(diff.keys())[0]).book.name)

        # shorts = sorted(diffs.items(), key=lambda x: (x[1], x[2]))[:10]
        print(diffs)

        with open("export2.csv", "w") as f:
            wr = csv.writer(f)
            book_ids = set()
            for _, diff in diffs:
                book_ids.update(list(diff.keys()))
            print("book_ids", book_ids)
            books_qs = Book.objects.filter(covers__in=book_ids).annotate(price_avg=Avg("prices__price"), price_count=Count("prices"))
            books = {book.pk: {"name": book.name, "avg": book.price_avg, "count": book.price_count} for book in books_qs}
            for path, diff in diffs:
                items = []
                for pk, val in list(diff.items())[:3]:
                    book = books.get(pk)
                    if book:
                        items += [book["name"], book["avg"], book["count"], pk, val]
                wr.writerow([path] + items)
