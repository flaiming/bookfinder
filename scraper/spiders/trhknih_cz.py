import scrapy
import re
from scraper.utils import make_full_url
from scraper.base_spider import BaseSpider


class TrhknihSpider(BaseSpider):
    name = 'trhknih_cz'
    allowed_domains = ['trhknih.cz']
    #download_delay = 1
    url_patern = "https://www.trhknih.cz/nabidky?page={page}&sort=a"

    def start_requests(self):
        yield scrapy.Request(url=self.url_patern.format(page=1), meta={"page": 1}, callback=self.parse_list)

    def parse_list(self, response):
        last_href = response.css(".pagination li a")[-1].extract()
        last_page = int(re.search(r"page=(\d+)&", last_href).group(1))

        item_count = 0
        for item in response.css(".bookitem"):
            profile_url = item.css("a.item-cover::attr(href)").extract_first()
            profile_url = make_full_url(response, profile_url)
            item_count += 1
            yield response.request.replace(url=profile_url, callback=self.parse_profile)

        new_page = response.meta["page"] + 1
        if new_page <= last_page:
            yield response.request.replace(url=self.url_patern.format(page=new_page), meta={"page": new_page}, callback=self.parse_list)

    def parse_profile(self, response):
        for row in response.css("#basic-table"):
            name = row.xpath("//h1/text()").extract_first(default="").strip()
            isbn = row.xpath('//*[@id="basic-table"]/table/tr/th[text()="ISBN"]/following-sibling::td/span/text()').extract_first(default="").strip()
            pages = row.xpath('//*[@id="basic-table"]/table/tr/th[text()="stran"]/following-sibling::td/text()').extract_first()
            year = row.xpath('//*[@id="basic-table"]/table/tr/th[text()="rok vydání"]/following-sibling::td/text()').extract_first()
            issue = row.xpath('//*[@id="basic-table"]/table/tr/th[text()="vydání"]/following-sibling::td/text()').extract_first()
            cover = make_full_url(response, response.css("#issue-cover img::attr(src)").extract_first())

            prices = []
            for row in response.css("#asks .ask-main-row")[1:]:
                orig_id = row.css(".asmaro::attr(data-ask-id)").extract_first()
                price = int(row.css(".ask-col-price > span > span::text").extract_first(default="").replace("Kč", "").strip())
                prices.append({"id": orig_id, "price": price, "price_type": "offer"})
            item = dict(
                name=name,
                isbn=isbn,
                pages=pages,
                year=year,
                issue=issue,
                cover=cover,
                profile_url=response.url,
                prices=prices,
            )
            yield item



