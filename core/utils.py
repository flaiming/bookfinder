import isbnlib


def clean_isbn(isbn):
    """
    Checks if ISBN is valid and converts it to ISBN13 format without dashes
    """
    if isbnlib.is_isbn10(isbn):
        return isbnlib.to_isbn13(isbn)
    elif isbnlib.is_isbn13(isbn):
        return isbnlib.canonical(isbn)
    # test if wrongly prefixed isbn10
    if isbn.startswith("978"):
        return clean_isbn(isbn[3:])
    return ""


def make_full_url(base_url, url):
    if not url:
        url = ""
    full_url = url
    domain = "/".join(base_url.split("/")[:3])
    if url.startswith("/"):
        full_url = domain + url
    elif not url.startswith("http"):
        full_url = domain + "/" + url
    return full_url

