# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

from matcher.models import Book, Author, BookCover


class ScraperPipeline:
    def process_item(self, item, spider):
        author = Author.objects.get_or_create(name=item["author"])[0]

        book = Book.objects.get_or_create(name=item["name"], author=author)[0]

        BookCover.objects.get_or_create(book=book, image_url=item["img"])
        return item


