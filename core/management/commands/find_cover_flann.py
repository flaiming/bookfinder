from PIL import Image
import os
import datetime

from django.core.management.base import BaseCommand
from django.db.models import Avg, Count
from .models import BookCover, Book
from .flann_matcher import FlannMatcher


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):

        matcher = None

        # load images to search
        images = []
        for image_name in os.listdir("_knihy"):

            # TEST ONLY
            #image_name = "DSC02524.JPG"

            image_path = os.path.join("_knihy", image_name)
            images.append(image_path)

        matcher = FlannMatcher(images)

        counter = 0
        ticker = datetime.datetime.now()
        #qs = BookCover.objects.exclude(image="").filter(book__name__icontains="bohatý táta").order_by("image").select_related("book")
        qs = BookCover.objects.exclude(image="").order_by("image").select_related("book")
        for cover in qs:
            #print(cover.book)
            #print(cover.image.path)

            try:
                counts = matcher.find_matches(cover.image.path)
            except Exception as e:
                #print("ERROR", e)
                continue
            if counts:
                print(counts)
                print(cover.book)

            if counter % 1000 == 0:
                print(counter, datetime.datetime.now() - ticker)
                ticker = datetime.datetime.now()
            counter += 1
