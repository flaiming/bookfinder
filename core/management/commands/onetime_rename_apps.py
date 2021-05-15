from django.core.management.base import BaseCommand, CommandError
from django.db import connection



class Command(BaseCommand):
    help = ""
    tables = [
        "author",
        "book",
        "book_authors",
        "bookcover",
        "bookimport",
        "bookprice",
        "bookprofile",
        "bookprofile_books",
        "source",
    ]

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            for table in self.tables:
                old_name = f"matcher_{table}"
                new_name = f"core_{table}"
                cursor.execute(f"ALTER TABLE {old_name} RENAME TO {new_name}")
                cursor.execute(f"ALTER TABLE {old_name}_id_seq RENAME TO {new_name}_id_seq")

            cursor.execute("UPDATE django_content_type SET app_label='core' WHERE app_label='matcher'")
