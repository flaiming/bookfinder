import scrapy
from bs4 import BeautifulSoup
from django.db.models import Count

from core.models import BookCover, BookPrice, BookPriceType, Source
from scraper.base_spider import BaseSpider


class DatabazeknihSpider(BaseSpider):
    name = 'databazeknih_prices'
    allowed_domains = ['databazeknih.cz']
    download_delay = 1
    source = None

    def start_requests(self):
        self.source = Source.objects.get_or_create(name="databazeknih.cz")[0]
        for cover in BookCover.objects.exclude(image_url="").annotate(cnt=Count("book__prices")).filter(cnt=0):
            orig_id = cover.get_orig_id()
            for price_type, price_type_str in ((BookPriceType.OFFER, "offer"), (BookPriceType.REQUEST, "request")):
                url = f"https://www.databazeknih.cz/book-detail-bazar.php?type={price_type_str}&bookId={orig_id}"
                yield scrapy.Request(url=url, meta={"book_id": cover.book_id, "price_type": price_type})

    def parse(self, response):
        bs = BeautifulSoup(response.text, 'html.parser')
        for row in bs.select("table.new tr"):
            tds = row.select("td")
            if len(tds) > 2:
                print(tds[1].contents[0])
                try:
                    price = int(tds[1].contents[0].replace("Kč", "").replace(" ", "").strip())
                except ValueError:
                    # ignore non-number values
                    continue
                print(price)
                bazar_id = tds[2].find("a")["href"].split("-")[-1]
                print(bazar_id)
                if price and bazar_id:
                    BookPrice.objects.update_or_create(
                        orig_id=bazar_id,
                        source=self.source,
                        book_id=response.meta["book_id"],
                        price_type=response.meta["price_type"],
                        defaults={"price": price}
                    )
