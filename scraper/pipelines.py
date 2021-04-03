# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import logging

from matcher.models import Book, Author, BookCover, BookProfile, BookPrice, BookPriceType
from matcher.bookmerger import BookMerger

logger = logging.getLogger()


class ScraperPipeline:
    def process_item(self, item, spider):

        for field in spider.required_fields:
            if not item.get(field):
                logger.warning(f"No '{field}' attribute in item of spider {spider}.")
                return

        book, status = BookMerger.create_if_not_exists(item)
        logger.info("%s book %s (ID %s)", "Created" if status == BookMerger.CREATED else "Updated", book, book.pk)
        return item


