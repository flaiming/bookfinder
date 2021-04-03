import re
from matcher.utils import make_full_url
from matcher.models import BookPriceType
from scraper.base_spider import BaseSpider


class CBDBSpider(BaseSpider):
    name = 'cbdb_cz'
    allowed_domains = ['cbdb.cz']
    download_delay = 0.5
    start_urls = ["https://www.cbdb.cz/knihy"]
    base_url = "https://www.cbdb.cz/"

    def parse(self, response):
        for letter in response.css("#content .textlist_item_select::attr(href)"):
            # TODO remove
            if letter.extract() == "knihy-0":
                continue
            href = self.base_url + letter.extract()
            yield response.request.replace(url=href, callback=self.parse_list)

    def parse_list(self, response):
        for row in response.css(".textlist tr"):
            href = row.css("td a::attr(href)").extract_first(default="")
            if href:
                href = self.base_url + href + "?show=bazar-knih"
                yield response.request.replace(url=href, callback=self.parse_profile)

        # get next page
        next_page_url = response.css("a.topic_paging_item[rel=next]::attr(href)").extract_first(default="")
        if next_page_url:
            next_page_url = self.base_url + next_page_url
            print(next_page_url)
            yield response.request.replace(url=next_page_url, callback=self.parse_list)

    def parse_profile(self, response):
        name = response.css("h1::text").extract_first(default="")
        cover = response.css("#book_photo_box img::attr(src)").extract_first(default="")
        if cover:
            cover = make_full_url(response.url, cover)
        authors = []
        for item in response.css("#book_author a"):
            author = item.css("*::text").extract_first(default="")
            authors.append(author)

        # parse prices
        prices = []
        for row in response.css(".subitem .textlist tr"):
            price_id = row.css(".insertions_list_photo a::attr(href)").extract_first(default="").split("-")[1]
            price_type = BookPriceType.OFFER if row.css("td.mobile_display_none::text").extract_first(default="").strip() == "Nabídka" else BookPriceType.REQUEST
            try:
                price = int(re.split(r"\s+", row.css("td::text").extract()[-1].strip())[0])
            except ValueError:
                continue
            prices.append({
                "id": price_id,
                "price_type": price_type,
                "price": price,
            })

        for row in response.css("#book_releases_area table tr"):
            if row.css("td")[0].attrib.get("class") == "book_releases_header":
                # skip header
                continue
            year = row.css("td::text").extract()[1].strip("()\n ")
            isbn = row.css("td")[1].css("::text").extract_first(default="").strip()
            pages = row.css("td")[2].css("::text").extract_first(default="").strip()
            yield dict(
                name=name,
                cover=cover,
                authors=authors,
                year=year,
                isbn=isbn,
                pages=pages,
                prices=prices,
                profile_url=response.url,
                deny_merge_on_fields=["profile_url"],
            )





