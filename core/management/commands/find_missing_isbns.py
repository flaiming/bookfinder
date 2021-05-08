from airtable import Airtable
from pprint import pprint
import logging
import xml.etree.ElementTree as ET

from urllib.parse import urlparse, parse_qs, unquote
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Avg, Q, Min, Max
from django.conf import settings

from .utils import clean_isbn
from .models import BookCover, Book, BookPriceType
from .xml_importer import XmlImporter, parse_profile_url
from .bookmerger import BookMerger
from .parsers import parse_price

logger = logging.getLogger()


class XmlReader(XmlImporter):

    def _import(self, file_name: str) -> int:
        try:
            tree = ET.parse(file_name)
        except IOError as e:
            logger.info(f"XmlImporter: Cannot open file {file_name} as XML: {e}")
            return False
        root = tree.getroot()

        # find items directly in root children
        child_counter = 0
        children_parent = None
        for child in root.getchildren()[:10]:
            if child.tag.lower() in self.children_node_names:
                child_counter += 1
                if child_counter >= 2:
                    # Bingo!
                    logger.info(f"XmlImporter: Parent of children is root: {root}")
                    children_parent = root
                    break
        if not children_parent:
            # find items in some root childrens
            child_counter = 0
            for child in root.getchildren()[:10]:
                for item in child.getchildren()[:10]:
                    if item.tag.lower() in self.children_node_names:
                        child_counter += 1
                        if child_counter >= 2:
                            # Bingo!
                            logger.info(f"XmlImporter: Parent of children id child of root: {child}")
                            children_parent = child
                            break
                if children_parent:
                    break

        if not children_parent:
            logger.warning("XmlImporter: Children parent not found!")
            return False

        for item in children_parent.getchildren():
            if item.tag.lower() in self.children_node_names:
                data = {"prices": [{"price_type": self.price_type}]}
                for elem in item:
                    tag = elem.tag.lower()
                    if "}" in tag:
                        tag = tag.split("}")[1]
                    for mapping in self.field_mapping:
                        xml_keys = mapping[1]
                        key = mapping[0]
                        fce = None
                        if len(mapping) == 3:
                            fce = mapping[2]
                        if self.custom_parsers.get(key):
                            fce = self.custom_parsers[key]
                        for tag_candidate in xml_keys:
                            if tag_candidate == tag:
                                if key in ("price", "id"):
                                    data["prices"][0][key] = fce(elem.text) if fce else elem.text
                                else:
                                    data[key] = fce(elem.text) if fce else elem.text
                                break
                # fix URL
                url = data.get("profile_url")
                if url and "?url=" in url:
                    url = unquote(url.split("?url=")[1])
                    data["profile_url"] = parse_profile_url(url)

                # set ISBN from EAN if exists
                if data.get("ean") and not data.get("isbn"):
                    data["isbn"] = data["ean"]

                yield data


class Command(BaseCommand):
    help = ""

    BASE_KEY = "appRoS86Vz8KKrQBt"
    TABLE_NAME = "Seznam knih"
    FIELD_MAPPING = {
        "name": "Název knihy",
        "isbn": "ISBN",
        "used_price": "Cena",
        "cover": "Přebal knihy",
    }
    OVERWRITABLE_FIELDS = (
        "offer_price_min",
        "offer_price_max",
        "offer_price",
        "offer_cnt",
        "price_offer",
        "price_request",
        "price_optimal",
        "new_price",
        "request_price_max",
        "used_price",
    )
    MULTIPLIER_FROM_NEW_PRICE = 0.7
    MULTIPLIER_FROM_OFFER_PRICE = 1.2

    def add_arguments(self, parser):
        parser.add_argument(
            "--save", action="store_true", default=False, help="Do not change data",
        )

        parser.add_argument(
            "--max-records", type=int, default=None, help="How many rows to update",
        )

    def process_page(self, page):
        records = {}
        for book in page:
            #print(book)
            isbn = clean_isbn(book["fields"].get("ISBN", {}).get("text", ""))
            if isbn:
                records.setdefault(isbn, [])
                data = {
                    "id": book["id"],
                }
                for key, name in self.FIELD_MAPPING.items():
                    if key == "isbn":
                        continue
                    data[key] = book["fields"].get(name)
                records[isbn].append(data)
        #print()
        #for k, v in records.items():
        #    print(k, v)

        # Load local books by ISBNs
        print("=============== Loading local books")
        books = {}
        qs = Book.objects.filter(isbn__in=records.keys()).annotate(
            offer_price=Avg("prices__price", filter=Q(prices__price_type=BookPriceType.OFFER)),
            offer_price_min=Min("prices__price", filter=Q(prices__price_type=BookPriceType.OFFER)),
            offer_price_max=Max("prices__price", filter=Q(prices__price_type=BookPriceType.OFFER)),
            offer_cnt=Count("prices", filter=Q(prices__price_type=BookPriceType.OFFER)),
            request_price=Avg("prices__price", filter=Q(prices__price_type=BookPriceType.REQUEST)),
            request_price_min=Min("prices__price", filter=Q(prices__price_type=BookPriceType.REQUEST)),
            request_price_max=Max("prices__price", filter=Q(prices__price_type=BookPriceType.REQUEST)),
            request_cnt=Count("prices", filter=Q(prices__price_type=BookPriceType.REQUEST)),
            used_price=Avg("prices__price", filter=Q(prices__profile__url__contains="reknihy.cz")),
            new_price=Max("prices__price", filter=Q(prices__price_type=BookPriceType.NEW)),
        ).prefetch_related("covers")
        for book in qs:
            try:
                book.cover = list(book.covers.all())[0].image_url
            except IndexError:
                book.cover = ""
            books[book.isbn] = book

        print("=============== Matching books")
        # Match airtable books to local books by ISBN
        rows_to_update = []
        for isbn, rows in records.items():
            book = books.get(isbn)
            if book:
                # Local book found!
                # update airtable rows
                for row in rows:
                    print("ROW", row)
                    fields = {}
                    for key, orig_val in row.items():
                        if key == "id":
                            continue
                        val = getattr(book, key, None)
                        if key == "author":
                            val = ", ".join(book.authors.values_list("name", flat=True)) or None
                        if key.startswith("price"):
                            val = int(val) if val else None
                        if key in ("price_offer", "price_request"):
                            price_type = key.split("_")[1]
                            if getattr(book, price_type + "_cnt") == 0:
                                val = None
                            else:
                                if price_type == "offer":
                                    if book.offer_price_min == book.offer_price_max:
                                        val = str(int(book.offer_price))
                                    else:
                                        val = f"{int(book.offer_price)} ({book.offer_price_min} - {book.offer_price_max} [{book.offer_cnt}])"
                                elif price_type == "request":
                                    if book.request_price_min == book.request_price_max:
                                        val = str(int(book.request_price))
                                    else:
                                        val = f"{int(book.request_price)} ({book.request_price_min} - {book.request_price_max} [{book.request_cnt}])"

                        elif key == "price_optimal":
                            if book.new_price:
                                val = int(book.new_price * self.MULTIPLIER_FROM_NEW_PRICE)
                            elif book.offer_price_max:
                                val = int(book.offer_price_max * self.MULTIPLIER_FROM_OFFER_PRICE)
                            elif book.request_price_max:
                                val = int(book.request_price_max)
                            else:
                                val = None
                        if key == "cover":
                            if val:
                                val = [{"url": val}]

                        if orig_val != val and (not orig_val or key in self.OVERWRITABLE_FIELDS):
                            fields[self.FIELD_MAPPING[key]] = val

                    if fields:
                        print("UPDATE", fields)
                        rows_to_update.append({"id": row["id"], "fields": fields})
        return rows_to_update

    def handle(self, *args, **options):
        save = options["save"]
        max_records = options["max_records"]

        reknihy = {}
        reader = XmlReader(BookPriceType.USED)
        for item in reader.import_from_file("reknihy-cz-google-nakupy-cz-e21d72bb7a3e15ff6c4c9e86a4495d10.xml"):
            isbn = item.get("isbn")
            if isbn:
                isbn_orig = isbn
                isbn = clean_isbn(isbn)
                reknihy.setdefault(isbn, [])
                item["isbn_orig"] = isbn_orig
                reknihy[isbn].append(item)

        print(f"reknihy num rows: {len(reknihy)}")

        airtable = Airtable(self.BASE_KEY, self.TABLE_NAME, settings.AIRTABLE_API_KEY)

        counter = 0
        unique_isbns = set()
        # Load data from airtable
        #for page in airtable.get_iter(fields=self.FIELD_MAPPING.values(), sort=["-ISBN"], pageSize=50, max_records=max_records, formula="FIND('9788087204870', {ISBN})=1"):
        for page in airtable.get_iter(fields=self.FIELD_MAPPING.values(), sort=["-ISBN"], pageSize=50, max_records=max_records, formula="AND({Název knihy}='', NOT({ISBN}=''))"):
            rows_to_update = []
            for book in page:
                #print(book)
                isbn_raw = book["fields"].get("ISBN", {}).get("text", "")
                isbn = clean_isbn(isbn_raw)
                if isbn:
                    unique_isbns.add(isbn)
                    data = {
                        "id": book["id"],
                        "isbn": isbn,
                    }
                    for key, name in self.FIELD_MAPPING.items():
                        if key == "isbn":
                            continue
                        data[key] = book["fields"].get(name)
                    found = reknihy.get(isbn)
                    if found:
                        print(f"airtable ISBN: {isbn}")
                        for f in found:
                            price = f["prices"][0]["price"]
                            name = f["name"]
                            cover = f["cover"]
                            fields_to_update = {}
                            if price != data["used_price"]:
                                print("--", f["name"], f["isbn_orig"])
                                print(f"price diff: {price} != {data['used_price']}")
                                fields_to_update[self.FIELD_MAPPING["used_price"]] = price
                            if not data["name"]:
                                fields_to_update[self.FIELD_MAPPING["name"]] = name
                            if not data["cover"]:
                                fields_to_update[self.FIELD_MAPPING["cover"]] = [{"url": cover}]

                            if fields_to_update:
                                rows_to_update.append({"id": book["id"], "fields": fields_to_update})
                                break
                else:
                    print(f"wrong ISBN {isbn_raw}")

            print()
            print(rows_to_update)

            print("=================== Data to update")
            pprint(rows_to_update)
            if rows_to_update and save:
                counter += len(rows_to_update)
                airtable.batch_update(rows_to_update)

        print(f"unique_isbns: {len(unique_isbns)}")

        print(f"Updated {counter} entries.")


