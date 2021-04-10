from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Avg, Q, Min, Max
from matcher.bookmerger import BookMerger
from matcher.models import BookCover, Book, BookPriceType
from urllib.parse import unquote

from matcher.xml_importer import XmlImporter


class Command(BaseCommand):
    help = ""

    #def add_arguments(self, parser):
    #    parser.add_argument(
    #        "-i", "--input", dest="input_file", type=str, help="Input CSV file",
    #    )

    def handle(self, *args, **options):

        #importer = XmlImporter(BookPriceType.NEW, custom_parsers={"name": lambda x: x.split(" - ")[0]})
        #importer.import_from_url(kosmas)

        #importer = XmlImporter(BookPriceType.USED)
        #counter = importer.import_from_url(reknihy)

        #importer = XmlImporter(BookPriceType.NEW, custom_parsers={"name": lambda x: x.split("|")[0].strip()})
        #counter = importer.import_from_url(albatros)

        importer = XmlImporter(BookPriceType.NEW, custom_parsers={
            "url": lambda x: unquote(x.split("?url=")[1]),
            "name": lambda x: x.split(" - ")[0],
        })
        counter = importer.import_from_file(dobrovsky_xml)
        print(f"Imported {counter} books.")
