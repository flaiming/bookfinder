import scrapy


class DatabazeknihSpider(scrapy.Spider):
    name = 'databazeknih'
    allowed_domains = ['databazeknih.cz']
    start_urls = ['https://www.databazeknih.cz/knihy']
    download_delay = 1

    def parse(self, response):
        # parse genres
        for zanr in response.css('select[name=zanr] option'):
            if not zanr.attrib.get("selected"):
                url = zanr.attrib.get("value")
                yield response.request.replace(url=url, callback=self.parse_list)

    def parse_list(self, response):
        for img_elem in response.css("img.inahled4"):
            img = img_elem.attrib["src"]
            if "/empty_n.jpg" in img:
                print("Empty image!")
                yield {}
            else:
                yield dict(
                    cover=img,
                    name=img_elem.attrib["title"],
                    url=img_elem.xpath("parent::a").attrib["href"],
                    author=img_elem.xpath("parent::a/following-sibling::span/text()").extract_first(),
                )
        # go to next page
        next_link = response.xpath('//span[@class="pnow"]/following-sibling::a')
        if next_link:
            url = next_link[0].attrib["href"]
            yield response.request.replace(url=url)
