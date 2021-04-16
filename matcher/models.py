import os
import requests
import logging
from io import BytesIO
from PIL import Image
import imagehash

from django.db import models
from django.core import files
from matcher.utils import clean_isbn

logger = logging.getLogger()


class Author(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.name


class Source(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Book(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    isbn = models.CharField(max_length=20, blank=True)
    pages = models.PositiveIntegerField(default=0)
    language = models.CharField(max_length=20, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)

    authors = models.ManyToManyField(Author, related_name="books")

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.isbn:
            # validate ISBN
            orig_isbn = self.isbn
            self.isbn = clean_isbn(self.isbn)
            if orig_isbn and not self.isbn:
                logger.warning(f"ISBN '{orig_isbn}' book with PK={self.pk} is not valid! Removing.")
        super().save(*args, **kwargs)


class BookProfile(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now_add=True)
    url = models.URLField(max_length=255, unique=True)

    books = models.ManyToManyField(Book, related_name="profiles")

    def __str__(self):
        return self.url


class BookPriceType(models.IntegerChoices):
    OFFER = 1
    REQUEST = 2
    NEW = 3
    USED = 4


class BookPrice(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    price = models.PositiveIntegerField()
    orig_id = models.CharField(max_length=20)
    price_type = models.PositiveIntegerField(choices=BookPriceType.choices)

    # TODO make not null in future
    profile = models.ForeignKey(BookProfile, on_delete=models.CASCADE, related_name="prices", null=True)
    # TODO remove book and source
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="prices")
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="prices", null=True)

    def __str__(self):
        return str(self.price)


def get_book_cover_image_path(instance, filename):
    name, ext = os.path.splitext(filename)
    if len(name) < 2:
        prefix1 = "a"
        prefix2 = "a"
    else:
        prefix1 = name[0]
        prefix2 = name[1]
    path = f"covers/{prefix1}/{prefix2}/{name}{ext}"
    return path


class BookCover(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to=get_book_cover_image_path, blank=True)
    image_url = models.URLField(max_length=255)

    hash_short = models.CharField(max_length=64, blank=True)
    hash_long = models.CharField(max_length=256, blank=True)

    book = models.ForeignKey(Book, related_name="covers", on_delete=models.CASCADE)
    # TODO make not null in future
    profile = models.ForeignKey(BookProfile, related_name="covers", on_delete=models.CASCADE, null=True)

    class Meta:
        ordering = ["-created"]

    def download_image(self):
        if self.image:
            # do not download image if already downloaded
            return
        resp = requests.get(self.image_url)
        if "/empty_n.jpg" in self.image_url:
            # remove default image of databazeknih
            if self.image and os.path.exists(self.image.path):
                os.remove(self.image.path)
            self.book.delete()
            return

        if resp.status_code == 404:
            logger.info(f"BookCover.download_image PK {self.pk}: URL {self.image_url} returned {resp.status_code}. Removing BookCover.")
            self.delete()
            return
        if resp.status_code != requests.codes.ok:
            raise Exception(f"Image cannot be downloaded {self.image_url}, {resp.status_code}, {resp}")

        fp = BytesIO()
        fp.write(resp.content)
        file_name = self.image_url.split("/")[-1]
        self.image.save(file_name, files.File(fp))
        # save BookCover to make image hashes
        self.save()

    def get_orig_id(self):
        try:
            return int(self.image_url.split(".")[-2].split('-')[-1])
        except ValueError:
            return None

    def save(self, *args, **kwargs):
        if self.image:
            if os.path.exists(self.image.path):
                # make image hashes
                img = Image.open(self.image.path)
                hash_short = imagehash.dhash(img, 16)
                hash_long = imagehash.dhash(img, 32)
                self.hash_short = hash_short
                self.hash_long = hash_long
                img.close()
        super().save(*args, **kwargs)


class BookImport(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True)
    name = models.CharField(max_length=50)
    url = models.TextField()
    price_type = models.PositiveIntegerField(choices=BookPriceType.choices)
    active = models.BooleanField(default=True)
    devider_in_name = models.CharField(max_length=1, blank=True)
    auth_user = models.CharField(max_length=20, blank=True)
    auth_password = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.name
