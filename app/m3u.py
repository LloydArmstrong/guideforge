"""Streaming M3U parsing for provider playlists."""
import re
from urllib.parse import urlsplit

from . import xmltv

_ATTR = re.compile(r'([\w-]+)="([^"]*)"')
_OURS = {"tvg-id", "tvg-name", "tvg-logo", "tvg-chno", "group-title"}  # rewritten on output; the rest pass through
_VOD = re.compile(r"/(movie|series)/|\.(mp4|mkv|avi|mov|flv|wmv)$", re.I)
_XTREAM = re.compile(r"(?:/live)?/[^/]+/[^/]+/(\d+)(?:\.\w+)?")


def stream_key(url):
    """A stable id for a stream: the Xtream stream number where there is one, so it survives a password change."""
    xtream = _XTREAM.fullmatch(urlsplit(url).path)
    return xtream[1] if xtream else url


def read_entries(path):
    """Yield one channel row per live stream, in playlist order."""
    # ponytail: live TV only. Provider playlists can carry 100k+ film and series entries, which the
    # editor cannot list and an M3U player shows poorly. Add a VOD pass-through if that is needed.
    with xmltv.open_xml(path) as f:
        info = None
        for raw in f:
            line = raw.decode("utf-8", "replace").strip()
            if line.startswith("#EXTINF"):
                info = line
            elif line and not line.startswith("#") and info is not None:
                if not _VOD.search(urlsplit(line).path):
                    attrs = dict(_ATTR.findall(info))
                    title = _ATTR.sub("", info).partition(",")[2].strip()
                    yield {
                        "id": stream_key(line),
                        "url": line,
                        "grp": attrs.get("group-title", "").strip(),
                        "up_name": title or attrs.get("tvg-name", ""),
                        "up_icon": attrs.get("tvg-logo") or None,
                        "up_lcn": attrs.get("tvg-chno") or None,
                        "up_tvg": attrs.get("tvg-id") or None,
                        "extra": " ".join(f'{k}="{v}"' for k, v in attrs.items() if k not in _OURS),
                    }
                info = None
