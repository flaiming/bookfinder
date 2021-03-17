

def make_full_url(response, url):
    if url is None:
        return ""
    full_url = url
    domain = "/".join(response.url.split("/")[:3])
    if url.startswith("/"):
        full_url = domain + url
    elif not url.startswith("http"):
        full_url = domain + "/" + url
    return full_url

