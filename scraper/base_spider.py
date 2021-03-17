import scrapy


class BaseSpider(scrapy.Spider):
    required_fields = ["profile_url", "name"]
