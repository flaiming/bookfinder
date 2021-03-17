# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import logging
import datetime

from matcher.models import Book, Author, BookCover, BookProfile, BookPrice, BookPriceType

logger = logging.getLogger()


class ScraperPipeline:
    def process_item(self, item, spider):

        for field in spider.required_fields:
            if not item.get(field):
                logger.warning(f"No '{field}' attribute in item of spider {spider}.")
                return

        author = None
        book_params = {"name": item["name"]}
        if item.get("author"):
            author = Author.objects.get_or_create(name=item["author"])[0]
            book_params["author"] = author
        for int_param in ("pages", "year"):
            if item.get(int_param):
                try:
                    val = int(item.get(int_param))
                except ValueError:
                    continue
                book_params[int_param] = val
        for str_param in ("language", ):
            if item.get(str_param):
                book_params[str_param] = item.get(str_param)

        if item.get("isbn"):
            # get book by ISBN
            book = Book.objects.get_or_create(isbn=item["isbn"], defaults=book_params)[0]
        elif author:
            # get book by name and author
            book = Book.objects.get_or_create(name=item["name"], author=author, **book_params)[0]
        else:
            logger.info(f"Item cannot be saved, too little params to deduplicate. {item}")
            return

        profile = BookProfile.objects.update_or_create(url=item["profile_url"], book=book, defaults={"last_updated": datetime.datetime.now()})[0]

        BookCover.objects.get_or_create(book=book, profile=profile, defaults=dict(image_url=item["cover"]))

        for price in item.get("prices", []):
            price_type = None
            if price["price_type"] == "offer":
                price_type = BookPriceType.OFFER
            elif price["price_type"] == "request":
                price_type = BookPriceType.REQUEST
            BookPrice.objects.update_or_create(orig_id=price["id"], profile=profile, book=book, price_type=price_type, defaults={"price": price["price"]})

        return item


