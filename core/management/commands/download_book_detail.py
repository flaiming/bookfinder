import os
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError
from .models import BookCover


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):

        detail_url = "https://www.databazeknih.cz/books/book-detail-more-info-ajax.php?bid={}"

        qs = BookCover.objects.filter(book__isbn="", book__pages=0).exclude(image_url="")
        print(qs.count())

        for cover in qs:
            try:
                print(cover.image_url)
                book_id = cover.get_orig_id()
                if not book_id:
                    print("ERROR getting book ID")
                    if os.path.exists(cover.image.path):
                        os.remove(cover.image.path)
                    cover.book.delete()
                    continue
                print(book_id)
                url = detail_url.format(book_id)
                resp = requests.get(url)
                print(resp.text)
                bs = BeautifulSoup(resp.text, 'html.parser')
                pages = bs.select_one("td[itemprop=numberOfPages]") or ""
                pages = int(pages.text or 0) if pages else 0
                language = bs.select_one("td[itemprop=language]")
                language = language.text if language else "český"
                isbn = bs.select_one("span[itemprop=isbn]") or ""
                isbn = isbn.text if isbn else ""
                print(isbn, language, pages)
                book = cover.book
                book.pages = pages
                book.language = "" if language == "český" else language
                book.isbn = isbn
                book.save()
            except Exception as e:
                print("ERROR", e)



