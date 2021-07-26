from bs4 import BeautifulSoup
from core.utils import make_full_url
from scraper.base_spider import BaseSpider


class DatabazeknihSpider(BaseSpider):
    name = 'databazeknih'
    allowed_domains = ['databazeknih.cz']
    start_urls = ['https://www.databazeknih.cz/knihy']
    #download_delay = 1

    custom_settings = {
        #"SKIP_FRESH_PROFILES": False,
    }

    def parse(self, response):

        if self.force_profile_url:
            yield response.request.replace(url=self.force_profile_url, callback=self.parse_profile)
            return

        # parse genres
        for zanr in response.css('select[name=zanr] option'):
            if not zanr.attrib.get("selected"):
                url = zanr.attrib.get("value")
                yield response.request.replace(url=url, callback=self.parse_list)

    def parse_list(self, response):
        for img_elem in response.css("img.inahled4"):
            url = make_full_url(response.url, img_elem.xpath("parent::a").attrib["href"])
            yield response.request.replace(url=url, callback=self.parse_profile)

        # go to next page
        next_link = response.xpath('//span[@class="pnow"]/following-sibling::a')
        if next_link:
            url = next_link[0].attrib["href"]
            yield response.request.replace(url=url)

    def parse_profile(self, response):
        bs = BeautifulSoup(response.text, 'html.parser')
        name = bs.select_one("h1[itemprop=name]").text
        authors = [a.text for a in bs.select("span[itemprop=author] a")]
        cover = bs.select_one(".kniha_img").get("src")
        year = bs.select_one("span[itemprop=datePublished]")
        if year:
            year = year.text
        meta = {
            "item": dict(
                name=name,
                authors=authors,
                cover=cover,
                year=year,
                profile_url=response.url,
            )
        }
        book_id = response.url.split("-")[-1]
        yield response.request.replace(
            url=f"https://www.databazeknih.cz/books/book-detail-more-info-ajax.php?bid={book_id}",
            callback=self.parse_more_info,
            meta=meta,
        )

    def parse_more_info(self, response):
        bs = BeautifulSoup(response.text, 'html.parser')
        pages = bs.select_one("td[itemprop=numberOfPages]")
        if pages:
            pages = pages.text
        isbn = bs.select_one("span[itemprop=isbn]")
        if isbn:
            isbn = isbn.text
        item = response.meta["item"]
        item["isbn"] = isbn
        item["pages"] = pages
        yield item
