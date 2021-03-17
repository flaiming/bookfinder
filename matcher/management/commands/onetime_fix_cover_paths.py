import shutil
import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from matcher.models import BookCover, get_book_cover_image_path


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        qs = BookCover.objects.exclude(image__iregex=r"^covers/[a-z0-9_-]/[a-z0-9_-]/")
        print(qs.count())

        counter = 0
        for cover in qs:
            path = cover.image.path
            name = cover.image.name.split("/")[-1].replace(".peg", ".jpeg")
            new_path = get_book_cover_image_path(cover, name)
            #print(path, "-->", new_path)
            new_path_abs = os.path.join(settings.MEDIA_ROOT, new_path)
            try:
                os.makedirs("/".join(new_path_abs.split("/")[:-1]))
            except OSError:
                pass
            try:
                shutil.copyfile(path, new_path_abs)
            except shutil.SameFileError:
                pass
            cover.image.name = new_path
            cover.save()
            os.remove(path)

            counter += 1
            if counter % 1000 == 0:
                print(counter)
