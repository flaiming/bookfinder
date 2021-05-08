from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Avg, Q, Min, Max
from .bookmerger import BookMerger
from .models import BookCover, Book, BookPriceType, BookImport
from urllib.parse import unquote

from .xml_importer import XmlImporter


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
            importer = XmlImporter(book_import.price_type, custom_parsers=custom_parsers, auth_user=book_import.auth_user, auth_password=book_import.auth_password)
            counter += importer.import_from_url(book_import.url)

        print(f"Imported {counter} books.")
