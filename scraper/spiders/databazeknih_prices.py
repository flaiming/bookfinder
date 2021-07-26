import scrapy
import datetime
from bs4 import BeautifulSoup
from django.db.models import Count

from core.models import BookCover, BookPrice, BookPriceType, Source, BookProfile
from scraper.base_spider import BaseSpider


class DatabazeknihSpider(BaseSpider):
    name = 'databazeknih_prices'
    allowed_domains = ['databazeknih.cz']
    download_delay = 1
    source = None

    def start_requests(self):
        self.source = Source.objects.get_or_create(name="databazeknih.cz")[0]
        for profile in BookProfile.objects.filter(url__contains="databazeknih.cz/").order_by("id"):
            orig_id = profile.url.split("-")[-1]
            for book in profile.books.all():
                for price_type, price_type_str in ((BookPriceType.OFFER, "offer"), (BookPriceType.REQUEST, "request")):
                    url = f"https://www.databazeknih.cz/book-detail-bazar.php?type={price_type_str}&bookId={orig_id}"
                    yield scrapy.Request(url=url, meta={"book": book, "price_type": price_type, "profile_url": profile.url})

    def parse(self, response):
        bs = BeautifulSoup(response.text, 'html.parser')
        prices = []
        for row in bs.select("table.new tr"):
            tds = row.select("td")
            if len(tds) > 2:
                print(tds[1].contents[0])
                try:
                    price = int(tds[1].contents[0].replace("Kč", "").replace(" ", "").strip())
                except ValueError:
                    # ignore non-number values
                    continue
                bazar_id = tds[2].find("a")["href"].split("-")[-1]
                if price and bazar_id:
                    prices.append([price, bazar_id])

        print(f"{prices=}")

        book = response.meta["book"]
        profile = BookProfile.objects.get(url=response.meta["profile_url"])
        # update last_updated
        profile.last_updated = datetime.datetime.now()
        profile.save(update_fields=['last_updated'])
        profile.books.add(book)

        for price, orig_id in prices:
            BookPrice.objects.update_or_create(
                orig_id=orig_id,
                profile=profile,
                book=book,
                price_type=response.meta["price_type"],
                defaults={
                    "price": price,
                    "source": self.source,
                }
            )
