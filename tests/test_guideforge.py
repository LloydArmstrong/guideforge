"""End-to-end check of ingest -> transform -> serve against a throwaway upstream.

Run: pip install httpx && python tests/test_guideforge.py
"""
import gzip
import os
import sys
import tempfile
import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

os.environ["DATA_DIR"] = tempfile.mkdtemp()
os.environ["ADMIN_PASSWORD"] = "pw"
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient  # noqa: E402
from lxml import etree  # noqa: E402

from app import db, sync, transform  # noqa: E402
from app.main import app  # noqa: E402

WWW = Path(tempfile.mkdtemp())


def upstream(*ids):
    """Publish a gzipped guide with two programmes per channel; returns its URL."""
    chans = "".join(
        f'<channel id="{i}"><display-name>{i.upper()}</display-name><icon src="http://logo/{i}.png"/></channel>\n'
        for i in ids
    )
    progs = "".join(
        f'<programme start="2026010{n}0000 +0000" channel="{i}"><title>Show {n} &amp; more</title></programme>\n'
        for i in ids
        for n in (1, 2)
    )
    (WWW / "guide.xml.gz").write_bytes(gzip.compress(f'<?xml version="1.0"?><tv>{chans}{progs}</tv>'.encode()))
    return f"http://127.0.0.1:{server.server_port}/guide.xml.gz"


def published():
    tv = etree.fromstring(gzip.decompress(db.OUTPUT.read_bytes()))
    return tv, [c.get("id") for c in tv.iter("channel")], [p.get("channel") for p in tv.iter("programme")]


def test_pipeline():
    db.init()
    db.put("upstream_url", upstream("a.uk", "b.uk", "c.us"))
    sync.sync()
    assert db.get("status")["error"] is None, db.get("status")
    _, chans, progs = published()
    assert chans == ["a.uk", "b.uk", "c.us"] and len(progs) == 6

    # layout: reorder, hide one channel, override another
    db.set_order(["c.us", "a.uk", "b.uk"])
    db.update_channels(["b.uk"], {"enabled": False})
    db.update_channels(["a.uk"], {"name": "BBC <One>", "lcn": "101", "icon": "http://x/y.png"})
    sync.rebuild()
    tv, chans, progs = published()
    assert chans == ["c.us", "a.uk"]
    assert progs == ["a.uk", "a.uk", "c.us", "c.us"]  # hidden channel's programmes are dropped
    a = tv.find("channel[@id='a.uk']")
    assert (a.findtext("display-name"), a.findtext("lcn"), a.find("icon").get("src")) == (
        "BBC <One>", "101", "http://x/y.png")
    assert tv.find("channel[@id='c.us']").findtext("display-name") == "C.US"  # untouched
    assert tv.findtext("programme/title") == "Show 1 & more"

    # upstream gains d.fr (appended, enabled) and e.uk... but a new channel in a fully disabled group stays hidden
    db.update_channels(["a.uk"], {"enabled": False})
    db.put("upstream_url", upstream("d.fr", "a.uk", "b.uk", "c.us", "e.uk"))
    sync.sync()
    order = [c["id"] for c in db.channels()]
    assert order == ["c.us", "a.uk", "b.uk", "d.fr", "e.uk"], order
    assert published()[1] == ["c.us", "d.fr"]

    # a channel that vanishes upstream is unpublished but keeps its place for when it returns
    db.put("upstream_url", upstream("d.fr"))
    sync.sync()
    assert published()[1] == ["d.fr"] and len(db.channels()) == 5

    # a broken upstream never replaces the published guide
    (WWW / "guide.xml.gz").write_bytes(b"<html>502 Bad Gateway</html>")
    sync.sync()
    assert "sync failed" in db.get("status")["error"]
    assert published()[1] == ["d.fr"]

    assert transform.guess_group("x", "UK: BBC One") == "UK" and transform.guess_group("espn.us", "ESPN") == "US"
    assert transform.guess_group("plain", "Plain") == ""


def test_serving():
    with TestClient(app) as http:
        token = db.tokens()[0]["token"]
        assert http.get("/epg.xml.gz").status_code == 403
        assert http.get("/epg.xml.gz?key=nope").status_code == 403

        r = http.get(f"/u/{token}/epg.xml.gz")
        assert r.status_code == 200 and r.headers["content-type"] == "application/x-gzip"
        assert "content-encoding" not in r.headers and r.content[:2] == b"\x1f\x8b"
        assert r.headers["access-control-allow-origin"] == "*" and r.headers["last-modified"]
        etag = r.headers["etag"]

        assert http.get(f"/epg.xml.gz?key={token}", headers={"If-None-Match": etag}).status_code == 304
        assert http.get(f"/epg.xml.gz?key={token}", headers={"If-None-Match": '"stale"'}).status_code == 200
        r = http.get(f"/epg.xml.gz?key={token}", headers={"If-Modified-Since": r.headers["last-modified"]})
        assert r.status_code == 304

        r = http.get(f"/epg.xml?key={token}", headers={"Accept-Encoding": "gzip"})
        assert r.headers["content-encoding"] == "gzip" and r.headers["content-type"] == "application/xml"
        assert r.text.startswith("<?xml")  # client transparently gunzips
        r = http.get(f"/epg.xml?key={token}", headers={"Accept-Encoding": "identity"})
        assert "content-encoding" not in r.headers and b'<channel id="d.fr">' in r.content
        assert http.head(f"/u/{token}/epg.xml").status_code == 200

        # management API: locked without the password, and layout edits flow through it
        assert http.get("/api/state").status_code == 401 and http.get("/").status_code == 401
        auth = ("admin", "pw")
        assert http.get("/api/state", auth=("admin", "wrong")).status_code == 401
        assert http.get("/").status_code == 401 and http.get("/", auth=auth).status_code == 200
        r = http.patch("/api/channels", auth=auth, json={"ids": ["d.fr"], "name": "  France 2 "})
        assert r.status_code == 200, r.text
        assert next(c for c in http.get("/api/channels", auth=auth).json() if c["id"] == "d.fr")["name"] == "France 2"
        assert http.patch("/api/channels", auth=auth, json={"ids": ["d.fr"], "position": 0}).status_code == 400
        assert http.put("/api/settings", auth=auth, json={
            "upstream_url": "file:///etc/passwd", "schedule": "6", "public_url": "", "public_access": False,
        }).status_code == 400
        blocked = http.post("/api/sync", auth=auth, headers={"Sec-Fetch-Site": "cross-site"})
        assert blocked.status_code == 403

        # revoking a key cuts that user off; public access opens the plain URL
        http.delete(f"/api/tokens/{token}", auth=auth)
        assert http.get(f"/u/{token}/epg.xml.gz").status_code == 403
        db.put("public_access", True)
        assert http.get("/epg.xml.gz").status_code == 200


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=WWW))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    test_pipeline()
    test_serving()
    print("ok")
