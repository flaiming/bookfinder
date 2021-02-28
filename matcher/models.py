from django.db import models
import requests
import logging
from django.core import files
from io import BytesIO

logger = logging.getLogger()


class Author(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.name


class Book(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    #isbn = models.CharField(max_length=20)

    author = models.ForeignKey(Author, related_name="books", on_delete=models.CASCADE)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.name


class BookCover(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to="covers", blank=True)
    image_url = models.URLField(max_length=255)

    hash_short = models.CharField(max_length=64, blank=True)
    hash_long = models.CharField(max_length=256, blank=True)

    book = models.ForeignKey(Book, related_name="covers", on_delete=models.CASCADE)

    class Meta:
        ordering = ["-created"]

    def download_image(self):
        resp = requests.get(self.image_url)

        if resp.status_code == 404:
            logger.info(f"BookCover.download_image PK {self.pk}: URL {self.image_url} returned {resp.status_code}")
            return
        if resp.status_code != requests.codes.ok:
            raise Exception(f"Image cannot be downloaded {self.image_url}, {resp.status_code}, {resp}")

        fp = BytesIO()
        fp.write(resp.content)
        file_name = self.image_url.split("/")[-1]  # There's probably a better way of doing this but this is just a quick example
        self.image.save(file_name, files.File(fp))
