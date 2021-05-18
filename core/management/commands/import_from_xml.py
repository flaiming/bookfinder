import logging
from urllib.parse import unquote

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Avg, Q, Min, Max
from core.bookmerger import BookMerger
from core.models import BookCover, Book, BookPriceType, BookImport
from core.xml_reader import XmlReader

logger = logging.getLogger()


class Command(BaseCommand):
    help = ""

    def add_arguments(self, parser):
        parser.add_argument(
            "--import", dest="import", type=int, help="Import ID",
        )

    def handle(self, *args, **options):
        import_id = options["import"]

        qs = BookImport.objects.filter(active=True)
        if import_id:
            qs = qs.filter(pk=import_id)

        counter = 0
        for book_import in qs:
            custom_parsers = {}
            if book_import.devider_in_name:
                custom_parsers["name"] = lambda x: x.split(f" {book_import.devider_in_name} ")[0].strip()
            importer = XmlReader(book_import.price_type, custom_parsers=custom_parsers, auth_user=book_import.auth_user, auth_password=book_import.auth_password)
            for row in importer.iter_rows_data(book_import.url):
                try:
                    book, status = BookMerger.create_if_not_exists(row)
                except AssertionError as e:
                    logger.warning(f"XmlReader: AssertionError: {e}")
                    # skip
                    continue
                print("UPDATED" if status == 2 else "CREATED", book)

        print(f"Imported {counter} books.")
