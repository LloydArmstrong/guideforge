"""Streaming XMLTV parsing: memory use stays flat however large the guide is."""
import gzip
from contextlib import contextmanager

from lxml import etree


@contextmanager
def open_xml(path):
    """Open a guide for reading, unwrapping gzip by magic bytes rather than file extension.

    Loops because a .xml.gz served with Content-Encoding: gzip arrives wrapped twice.
    """
    with open(path, "rb") as raw:
        f = raw
        while f.peek(2)[:2] == b"\x1f\x8b":
            f = gzip.GzipFile(fileobj=f)
        yield f


def iter_elements(path):
    """Yield every <channel> and <programme> in document order, freeing each one afterwards.

    Both tags are always visited, even when the caller wants only one: an element
    that is never yielded is never freed, and the tree would grow to the whole file.
    """
    with open_xml(path) as f:
        # recover: IPTV guides are routinely slightly malformed. resolve_entities off: no XXE.
        events = etree.iterparse(
            f, tag=("channel", "programme"), recover=True, huge_tree=True, resolve_entities=False
        )
        for _, el in events:
            yield el
            el.clear()
            while el.getprevious() is not None:
                del el.getparent()[0]


def read_channels(path):
    """Yield {id, name, icon, lcn, xml} for each upstream <channel>."""
    for el in iter_elements(path):
        if el.tag == "channel" and el.get("id"):
            icon = el.find("icon")
            yield {
                "id": el.get("id"),
                "name": el.findtext("display-name") or "",
                "icon": icon.get("src") if icon is not None else None,
                "lcn": el.findtext("lcn"),
                "xml": etree.tostring(el, encoding="unicode", with_tail=False),
            }
