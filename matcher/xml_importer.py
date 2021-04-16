import os
import re
import zipfile
import requests
import tempfile
import shutil
import logging
from typing import Optional
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, parse_qs, unquote
from matcher.bookmerger import BookMerger, BookPriceType
from matcher.parsers import parse_price

logger = logging.getLogger(__name__)


def parse_profile_url(url: str) -> str:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    attr = qs.get('attribute_pa_vazba')
    if attr:
        return url.split("?")[0] + "?attribute_pa_vazba=" + attr[0]
    return url.split("?")[0]


class XmlImporter:
    children_node_names = ("item", "product", "shopitem", "entry")
    field_mapping = {
        ("name", ("product", "productname", "name", "title")),
        ("id", ("pid", "item_id", "code", "id")),
        ("profile_url", ("url", "product_url", "link")),
        ("price", ("sale_price", "price", "price_vat", "final_price"), parse_price),
        ("cover", ("imgurl", "imgurl_alternative", "image_url", "image", "image_link")),
        ("ean", ("ean", )),
        ("isbn", ("gtin", "isbn")),
    }

    def __init__(self, price_type: BookPriceType, custom_parsers: Optional[dict] = None, auth_user: Optional[str] = None, auth_password: Optional[str] = None) -> None:
        self.price_type = price_type
        self.custom_parsers = custom_parsers or {}
        self.auth_user = auth_user
        self.auth_password = auth_password

    def import_from_url(self, import_url: str) -> int:
        temp_dir = tempfile.gettempdir()
        temp_file = "%s" % os.path.join(temp_dir, re.sub(r'[^a-z_-]+', '', import_url.replace('/', '_'), flags=re.I | re.U))
        if not os.path.exists(temp_file):
            logger.info("Downloading file from URL %s.", str(import_url))

            headers = {
                'User-agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
            }
            auth = None
            if self.auth_user:
                auth = (self.auth_user, self.auth_password)
            resp = requests.get(import_url, headers=headers, stream=True, auth=auth)
            with open(temp_file, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=1024):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
                        f.flush()
                        os.fsync(f.fileno())

            if zipfile.is_zipfile(temp_file):
                with zipfile.ZipFile(temp_file, 'r') as z:
                    for name in z.namelist():
                        zipped_dir = os.path.join(temp_dir, 'zipped_feeds')
                        if not os.path.exists(zipped_dir):
                            os.makedirs(zipped_dir)
                        z.extract(name, zipped_dir)
                        shutil.move(os.path.join(zipped_dir, name), temp_file)
        return self._import(temp_file)

    def import_from_file(self, file_name: str) -> int:
        return self._import(file_name)

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

        counter = 0
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

                print(data)
                counter += 1
                try:
                    book, status = BookMerger.create_if_not_exists(data)
                except AssertionError as e:
                    logger.warning(f"XmlImporter: AssertionError: {e}")
                    # skip
                    continue
                print("UPDATED" if status == 2 else "CREATED", book)
        return counter

