"""Tells IndexNow which pages changed: Bing, Yandex, Seznam, Naver and the other engines that share it.
Dev only, standard library. The key file at the site root proves the site is ours, so send only once it is live.

    python tools/indexnow.py                # dry run: print the payload for every <loc> in sitemap.xml
    python tools/indexnow.py URL [URL ...]  # dry run for these pages only
    python tools/indexnow.py --send         # POST it to IndexNow and print the HTTP status
"""
import argparse
import json
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = "getrackup.com"
KEY = "0a9442a5613cbbd088b30f789f206e74"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"
SITEMAP = ROOT / "sitemap.xml"
LOC = "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
# The answers documented at https://www.indexnow.org/documentation
MEANING = {200: "submitted", 202: "accepted, the key is still being checked", 400: "bad request",
           403: f"key not valid; is {KEY_LOCATION} live?", 422: f"a URL is not on {HOST}, or the key does not match",
           429: "too many requests"}


def sitemap_urls(path=SITEMAP):
    return [loc.text.strip() for loc in ET.parse(str(path)).getroot().iter(LOC)]


def payload(urls):
    return {"host": HOST, "key": KEY, "keyLocation": KEY_LOCATION, "urlList": list(urls)}


def request_for(body):
    return urllib.request.Request(ENDPOINT, data=json.dumps(body).encode("utf-8"), method="POST",
                                  headers={"Content-Type": "application/json; charset=utf-8"})


def send(body):
    """POSTs the payload and returns the HTTP status, which IndexNow also uses for its refusals."""
    try:
        with urllib.request.urlopen(request_for(body), timeout=30) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("urls", nargs="*", metavar="URL", help="pages to submit instead of the whole sitemap")
    parser.add_argument("--send", action="store_true", help="POST to IndexNow; without it nothing leaves this machine")
    args = parser.parse_args(argv)
    urls = args.urls or sitemap_urls()
    elsewhere = [u for u in urls if not u.startswith(f"https://{HOST}/")]
    if elsewhere:
        parser.error(f"not on https://{HOST}/: {' '.join(elsewhere)}")
    body = payload(urls)
    if not args.send:
        print(f"Dry run, nothing sent. With --send this goes to {ENDPOINT}:")
        print(json.dumps(body, indent=1))
        return 0
    status = send(body)
    print(f"HTTP {status}: {MEANING.get(status, 'see https://www.indexnow.org/documentation')}")
    return 0 if status in (200, 202) else 1


if __name__ == "__main__":
    sys.exit(main())
