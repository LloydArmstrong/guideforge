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

from app import db, m3u, sync, transform  # noqa: E402
from app.main import app  # noqa: E402

WWW = Path(tempfile.mkdtemp())


def url(name):
    return f"http://127.0.0.1:{server.server_port}/{name}"


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
    return url("guide.xml.gz")


def provider(password="pass"):
    """Publish an Xtream-style playlist: three live channels and one film; returns its URL."""
    (WWW / "get.php").write_text(
        "#EXTM3U\n"
        '#EXTINF:-1 tvg-id="d.fr" tvg-name="FR: France 2" tvg-logo="http://logo/f2.png" group-title="France" timeshift="3",FR: France 2\n'
        f"http://prov:8080/live/user/{password}/101.ts\n"
        '#EXTINF:-1 tvg-id="" group-title="UK",UK: Mystery "One"\n'
        f"http://prov:8080/live/user/{password}/102.ts\n"
        '#EXTINF:-1 tvg-id="x.film" group-title="Films",Some Film\n'
        f"http://prov:8080/movie/user/{password}/900.mkv\n"
        '#EXTINF:-1 tvg-id="c.us" group-title="USA",US: CNN\n'
        f"http://prov:8080/user/{password}/103\n"
    )
    return url("get.php")


def guide():
    tv = etree.fromstring(gzip.decompress(db.OUTPUT.read_bytes()))
    return tv, [c.get("id") for c in tv.iter("channel")], [p.get("channel") for p in tv.iter("programme")]


def playlist():
    """The published playlist as (info line, stream url) pairs."""
    lines = db.PLAYLIST.read_text().splitlines()
    return list(zip(lines[::2], lines[1::2]))


def test_guide_only():
    db.init()
    db.put("upstream_url", upstream("a.uk", "b.uk", "c.us"))
    sync.sync()
    assert db.get("status")["error"] is None, db.get("status")
    _, chans, progs = guide()
    assert chans == ["a.uk", "b.uk", "c.us"] and len(progs) == 6
    assert db.groups() == ["UK", "US"] and not db.PLAYLIST.exists()

    # layout: reorder groups and channels, hide one channel, override another
    db.set_groups(["US", "UK"])
    db.set_order(["b.uk", "a.uk"])
    db.update_channels(["b.uk"], {"enabled": False})
    db.update_channels(["a.uk"], {"name": "BBC <One>", "lcn": "101", "icon": "http://x/y.png"})
    assert guide()[1] == ["a.uk", "b.uk", "c.us"]  # editing publishes nothing
    sync.sync()
    tv, chans, progs = guide()
    assert chans == ["c.us", "a.uk"]
    assert progs == ["a.uk", "a.uk", "c.us", "c.us"]  # hidden channel's programmes are dropped
    a = tv.find("channel[@id='a.uk']")
    assert (a.findtext("display-name"), a.findtext("lcn"), a.find("icon").get("src")) == (
        "BBC <One>", "101", "http://x/y.png")
    assert tv.find("channel[@id='c.us']").findtext("display-name") == "C.US"  # untouched
    assert tv.findtext("programme/title") == "Show 1 & more"

    # new channels join the end of their group, new groups come last,
    # and a channel arriving in a group that is switched off entirely stays off
    db.update_channels(["a.uk"], {"enabled": False})
    db.put("upstream_url", upstream("d.fr", "a.uk", "b.uk", "c.us", "e.uk"))
    sync.sync()
    assert [c["id"] for c in db.channels()] == ["c.us", "b.uk", "a.uk", "e.uk", "d.fr"]
    assert guide()[1] == ["c.us", "d.fr"]

    # a channel that vanishes upstream is unpublished but keeps its place for when it returns
    db.put("upstream_url", upstream("d.fr"))
    sync.sync()
    assert guide()[1] == ["d.fr"] and len(db.channels()) == 5

    # a broken upstream never replaces the published guide...
    (WWW / "guide.xml.gz").write_bytes(b"<html>502 Bad Gateway</html>")
    sync.sync()
    assert "sync failed" in db.get("status")["error"]
    assert guide()[1] == ["d.fr"]
    # ...but edits that were waiting still go out, from the last good download
    db.update_channels(["d.fr"], {"name": "France 2"})
    sync.mark_dirty()
    sync.sync()
    assert "sync failed" in db.get("status")["error"] and not db.get("dirty")
    assert guide()[0].find("channel[@id='d.fr']").findtext("display-name") == "France 2"

    assert transform.guess_group("x", "UK: BBC One") == "UK" and transform.guess_group("espn.us", "ESPN") == "US"
    assert transform.guess_group("plain", "Plain") == ""


def test_playlist():
    assert m3u.stream_key("http://h/live/u/p/7.ts") == m3u.stream_key("http://other/u/new/7") == "7"
    assert m3u.stream_key("http://h/tv/index.m3u8") == "http://h/tv/index.m3u8"

    db.put("upstream_url", upstream("d.fr", "c.us", "zz.uk"))
    db.put("playlist_url", provider())
    sync.sync()
    assert db.get("status")["error"] is None, db.get("status")
    assert set(db.groups()) >= {"France", "UK", "USA"}  # the provider's own groups, films left out
    db.set_groups(["France", "UK", "USA"])  # also sweeps away groups emptied when the playlist replaced guide-only rows
    assert db.groups() == ["France", "UK", "USA"]
    sync.sync()
    assert [(c["id"], c["grp"], c["up_tvg"]) for c in db.channels()] == [
        ("101", "France", "d.fr"), ("102", "UK", None), ("103", "USA", "c.us")]
    info, stream = playlist()[0]
    assert stream == "http://prov:8080/live/user/pass/101.ts"
    assert info == ('#EXTINF:-1 tvg-id="d.fr" tvg-name="FR: France 2" tvg-logo="http://logo/f2.png"'
                    ' group-title="France" timeshift="3",FR: France 2')  # unknown attributes pass through
    assert playlist()[1][0] == """#EXTINF:-1 tvg-name="UK: Mystery 'One'" group-title="UK",UK: Mystery 'One'"""
    assert guide()[1] == ["d.fr", "c.us"]  # only guide channels a published stream points at

    # the whole point: groups and order are the operator's
    db.set_groups(["Favourites", "France", "UK", "USA"])  # a new, empty group, put first
    db.update_channels(["103"], {"grp": "Favourites", "name": "CNN"})
    db.update_channels(["102"], {"tvg": "zz.uk"})  # point a stream at the guide channel that describes it
    db.rename_group("France", "FR")
    db.update_channels(["101"], {"enabled": False})
    sync.sync()
    assert [(i.rpartition(",")[2], i.split('group-title="')[1].split('"')[0]) for i, _ in playlist()] == [
        ("CNN", "Favourites"), ("UK: Mystery 'One'", "UK")]
    assert 'tvg-id="zz.uk"' in playlist()[1][0]
    assert guide()[1] == ["c.us", "zz.uk"]
    db.set_groups(["Favourites", "UK"])  # USA is empty and goes; FR still has a channel, so it stays
    assert db.groups() == ["Favourites", "UK", "FR"]

    # a new provider password changes every stream address, but the line-up survives
    db.put("playlist_url", provider("hunter2"))
    sync.sync()
    assert [(c["id"], c["grp"], c["name"]) for c in db.channels()] == [
        ("103", "Favourites", "CNN"), ("102", "UK", None), ("101", "FR", None)]
    assert playlist()[0][1] == "http://prov:8080/user/hunter2/103"
    assert not list(db.DATA.glob("*.download"))  # the raw playlist, with its login, is not kept


def test_serving():
    with TestClient(app) as http:
        token = db.tokens()[0]["token"]
        assert http.get("/epg.xml.gz").status_code == 403
        assert http.get("/epg.xml.gz?key=nope").status_code == 403
        assert http.get("/playlist.m3u").status_code == 403

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
        assert "content-encoding" not in r.headers and b'<channel id="c.us">' in r.content
        assert http.head(f"/u/{token}/epg.xml").status_code == 200

        # the playlist carries this viewer's guide address, so one URL sets up a player
        r = http.get(f"/u/{token}/playlist.m3u")
        assert r.status_code == 200 and r.headers["content-type"].startswith("audio/x-mpegurl")
        assert r.text.splitlines()[0] == f'#EXTM3U url-tvg="http://testserver/u/{token}/epg.xml.gz"'
        assert r.text.splitlines()[2] == "http://prov:8080/user/hunter2/103"
        assert http.get(f"/playlist.m3u?key={token}", headers={"If-None-Match": r.headers["etag"]}).status_code == 304

        # management API: locked without the password
        assert http.get("/api/state").status_code == 401 and http.get("/").status_code == 401
        auth = ("admin", "pw")
        assert http.get("/api/state", auth=("admin", "wrong")).status_code == 401
        assert http.get("/").status_code == 401 and http.get("/", auth=auth).status_code == 200
        blocked = http.post("/api/sync", auth=auth, headers={"Sec-Fetch-Site": "cross-site"})
        assert blocked.status_code == 403

        # edits are saved and flagged as waiting; nothing is fetched or published until a sync
        published = http.get("/api/state", auth=auth).json()["status"]["built_at"]
        r = http.patch("/api/channels", auth=auth, json={"ids": ["102"], "name": "  Mystery ", "grp": "Favourites"})
        assert r.status_code == 200, r.text
        assert http.put("/api/groups", auth=auth, json=["Kids", "Favourites", "UK", "FR"]).json()[0] == "Kids"
        assert http.post("/api/groups/rename", auth=auth, json={"old": "FR", "new": "France"}).status_code == 200
        assert http.put("/api/settings", auth=auth, json={
            "playlist_url": db.get("playlist_url"), "upstream_url": db.get("upstream_url"),
            "schedule": "24", "public_url": "", "public_access": False,
        }).status_code == 200
        state = http.get("/api/state", auth=auth).json()
        assert state["dirty"] and state["running"] is None and state["status"]["built_at"] == published
        assert "Mystery" not in db.PLAYLIST.read_text().replace("UK: Mystery", "")
        listing = http.get("/api/channels", auth=auth).json()
        assert listing["groups"] == ["Kids", "Favourites", "UK", "France"]
        assert [(c["id"], c["grp"], c["name"]) for c in listing["channels"]][:2] == [
            ("102", "Favourites", "Mystery"), ("103", "Favourites", "CNN")]  # the editor then saves where it was dropped
        assert ["zz.uk", "ZZ.UK"] in listing["guide"]
        sync.sync()
        assert not http.get("/api/state", auth=auth).json()["dirty"] and ",Mystery\n" in db.PLAYLIST.read_text()

        assert http.patch("/api/channels", auth=auth, json={"ids": ["102"], "position": 0}).status_code == 400
        assert http.put("/api/settings", auth=auth, json={
            "playlist_url": "file:///etc/passwd", "upstream_url": "", "schedule": "24", "public_url": "",
            "public_access": False,
        }).status_code == 400

        # revoking a key cuts that user off; public access opens the plain URLs
        http.delete(f"/api/tokens/{token}", auth=auth)
        assert http.get(f"/u/{token}/epg.xml.gz").status_code == 403
        assert http.get(f"/u/{token}/playlist.m3u").status_code == 403
        db.put("public_access", True)
        assert http.get("/epg.xml.gz").status_code == 200
        r = http.get('/u/"%0Ainjected/playlist.m3u')
        assert r.text.splitlines()[0] == '#EXTM3U url-tvg="http://testserver/epg.xml.gz"'  # unchecked keys are not echoed


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=WWW))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    test_guide_only()
    test_playlist()
    test_serving()
    print("ok")
