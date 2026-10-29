"""Ingestion: stream the upstream guide to disk."""
import urllib.request
from urllib.parse import urlsplit

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; GuideForge/1.0)", "Accept-Encoding": "gzip"}


def fetch(url, dest, progress=None):
    """Download url to dest without holding it in memory; returns the size in bytes.

    The body is stored as received. Whether it is .xml, .xml.gz or gzip
    transfer-encoded is sorted out by xmltv.open_xml from the magic bytes.
    progress(done, total) is called as bytes arrive; total is 0 when the server does not say.
    """
    if urlsplit(url).scheme not in ("http", "https"):  # urllib would happily open file:// too
        raise ValueError("upstream URL must start with http:// or https://")
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=60) as response, open(dest, "wb") as out:
        total, done = int(response.headers.get("Content-Length") or 0), 0
        while chunk := response.read1(1 << 20):  # read1: whatever has arrived, so the count keeps moving on a slow line
            out.write(chunk)
            done += len(chunk)
            if progress:
                progress(done, total)
    return dest.stat().st_size
