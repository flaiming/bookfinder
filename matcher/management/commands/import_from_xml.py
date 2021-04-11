from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Avg, Q, Min, Max
from matcher.bookmerger import BookMerger
from matcher.models import BookCover, Book, BookPriceType, BookImport
from urllib.parse import unquote

from matcher.xml_importer import XmlImporter


class Command(BaseCommand):
    help = ""

    #def add_arguments(self, parser):
    #    parser.add_argument(
    #        "-i", "--input", dest="input_file", type=str, help="Input CSV file",
    #    )

    def handle(self, *args, **options):

        counter = 0
        for book_import in BookImport.objects.filter(active=True):
            custom_parsers = {}
            if book_import.devider_in_name:
                custom_parsers["name"] = lambda x: x.split(f" {book_import.devider_in_name} ")[0].strip()
            importer = XmlImporter(BookPriceType.NEW, custom_parsers=custom_parsers)
            counter += importer.import_from_url(book_import.url)

        print(f"Imported {counter} books.")

