import csv
import isbnlib
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, parse_qs
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Avg, Q, Min, Max
from .bookmerger import BookMerger
from .models import BookCover, Book, BookPriceType


class Command(BaseCommand):
    help = ""

    #def add_arguments(self, parser):
    #    parser.add_argument(
    #        "-i", "--input", dest="input_file", type=str, help="Input CSV file",
    #    )

    def handle(self, *args, **options):
        #input_file = options["input_file"]
        input_file = "reknihy-cz-google-nakupy-cz-e21d72bb7a3e15ff6c4c9e86a4495d10.xml"
        print(input_file)

        def parse_profile_url(url):
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)
            attr = qs.get('attribute_pa_vazba')
            if attr:
                return url.split("?")[0] + "?attribute_pa_vazba=" + attr[0]
            return url.split("?")[0]

        field_mapping = {
            ("id", "id"),
            ("title", "name"),
            ("link", "profile_url", parse_profile_url),
            ("image_link", "cover"),
            ("price", "price", lambda x: x.split()[1].split(",")[0]),
            ("gtin", "isbn"),
        }

        tree = ET.parse(input_file)
        root = tree.getroot()
        channel = root.getchildren()[0]
        for item in channel.getchildren():
            if item.tag == "item":
                data = {"prices": [{"price_type": BookPriceType.USED}]}
                for elem in item:
                    tag = elem.tag
                    if "}" in tag:
                        tag = tag.split("}")[1]
                    for mapping in field_mapping:
                        xml_key = mapping[0]
                        key = mapping[1]
                        fce = None
                        if len(mapping) == 3:
                            fce = mapping[2]
                        if tag == xml_key:
                            if tag in ("price", "id"):
                                data["prices"][0][key] = fce(elem.text) if fce else elem.text
                            else:
                                data[key] = fce(elem.text) if fce else elem.text

                print(data)
                book, status = BookMerger.create_if_not_exists(data)
                print("UPDATED" if status == 2 else "CREATED", book)

