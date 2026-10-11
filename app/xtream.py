"""Reading a provider's live channels through the Xtream Codes player API."""
import json
import urllib.request
from urllib.parse import quote, urlsplit

from . import ingest


def server_root(url):
    """Reduce whatever was pasted (host:port, or a whole get.php link) to scheme://host:port; '' if unusable."""
    url = url.strip()
    if url and "://" not in url:
        url = "http://" + url
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}" if parts.scheme in ("http", "https") and parts.netloc else ""


def call(server, username, password, **params):
    """One player_api.php request; returns the decoded JSON."""
    query = "&".join(f"{k}={quote(str(v), safe='')}" for k, v in {"username": username, "password": password, **params}.items())
    request = urllib.request.Request(f"{server}/player_api.php?{query}", headers={"User-Agent": ingest.HEADERS["User-Agent"]})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def read_channels(server, username, password):
    """Yield one channel row per live stream, in the provider's own group and channel order.

    Rows are keyed by stream id, the same key m3u.stream_key gives, so a line-up
    built from an M3U link carries over.
    """
    account = call(server, username, password)
    if not isinstance(account, dict) or str((account.get("user_info") or {}).get("auth")) != "1":
        raise ValueError("the provider did not accept that username and password")
    categories = call(server, username, password, action="get_live_categories")
    streams = call(server, username, password, action="get_live_streams")
    if not isinstance(categories, list) or not isinstance(streams, list):
        raise ValueError("the provider did not return a channel list")
    names = {str(c.get("category_id")): (c.get("category_name") or "").strip() for c in categories}
    rank = {category_id: n for n, category_id in enumerate(names)}
    streams.sort(key=lambda s: rank.get(str(s.get("category_id")), len(rank)))  # stable: order inside a category is kept
    user, secret = quote(username, safe=""), quote(password, safe="")
    for s in streams:
        yield {
            "id": str(s["stream_id"]),
            "url": f"{server}/live/{user}/{secret}/{s['stream_id']}.ts",
            "grp": names.get(str(s.get("category_id")), ""),
            "up_name": (s.get("name") or "").strip(),
            "up_icon": s.get("stream_icon") or None,
            "up_lcn": None,  # the API's "num" is a running index, not a channel number
            "up_tvg": s.get("epg_channel_id") or None,
            "extra": "",
        }
