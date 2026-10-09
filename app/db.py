"""SQLite persistence: channel layout, groups, guide channels, settings and access tokens."""
import json
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DATA = Path(os.environ.get("DATA_DIR", "data"))
DB = DATA / "guideforge.db"
UPSTREAM = DATA / "upstream.cache"  # last good guide download, exactly as received
OUTPUT = DATA / "epg.xml.gz"  # the published guide
PLAYLIST = DATA / "playlist.m3u"  # the published playlist, minus its #EXTM3U line (serve.py writes that per viewer)

SCHEMA = """
CREATE TABLE IF NOT EXISTS channels (
    id       TEXT PRIMARY KEY,            -- playlist stream key, or the XMLTV channel id when there is no playlist
    position INTEGER NOT NULL,            -- order inside its group
    enabled  INTEGER NOT NULL DEFAULT 1,
    present  INTEGER NOT NULL DEFAULT 1,  -- seen in the latest upstream sync
    grp      TEXT NOT NULL DEFAULT '',
    url      TEXT,                        -- stream address; NULL for a guide-only channel
    extra    TEXT,                        -- playlist attributes passed through untouched (catch-up and the like)
    up_name  TEXT, up_icon TEXT, up_lcn TEXT, up_tvg TEXT,  -- as last seen upstream
    name     TEXT, icon TEXT, lcn TEXT, tvg TEXT            -- overrides; NULL means "use upstream"
);
CREATE INDEX IF NOT EXISTS channels_grp ON channels (grp, enabled);
-- Players list groups in this order, and channels by position inside each.
CREATE TABLE IF NOT EXISTS groups (name TEXT PRIMARY KEY, position INTEGER NOT NULL);
-- The upstream guide's channels, replaced on every sync. A channel gets guide data when its tvg id matches one.
CREATE TABLE IF NOT EXISTS epg_channels (id TEXT PRIMARY KEY, name TEXT, xml TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS tokens (token TEXT PRIMARY KEY, label TEXT NOT NULL, created TEXT NOT NULL);
"""

# A database from before playlists existed: its channels are guide-only, keyed by their XMLTV id.
MIGRATE_V1 = """
ALTER TABLE channels ADD COLUMN url TEXT;
ALTER TABLE channels ADD COLUMN extra TEXT;
ALTER TABLE channels ADD COLUMN up_tvg TEXT;
ALTER TABLE channels ADD COLUMN tvg TEXT;
UPDATE channels SET up_tvg = id;
ALTER TABLE channels DROP COLUMN xml;
"""

# Env vars only seed first-run defaults; values saved from the UI win.
DEFAULTS = {
    "playlist_url": os.environ.get("PLAYLIST_URL", ""),
    "upstream_url": os.environ.get("UPSTREAM_URL", ""),
    "schedule": os.environ.get("SYNC_SCHEDULE", "0 4 * * *"),
    "public_url": os.environ.get("PUBLIC_URL", "").rstrip("/"),
    "public_access": False,
    "status": {},
    "dirty": False,  # layout edits made since the last publish
}
EDITABLE = {"enabled", "grp", "name", "icon", "lcn", "tvg"}

_UPSERT = """
INSERT INTO channels (id, position, enabled, grp, url, extra, up_name, up_icon, up_lcn, up_tvg)
VALUES (:id, :position, COALESCE((SELECT MAX(enabled) FROM channels WHERE grp = :grp), 1),
        :grp, :url, :extra, :up_name, :up_icon, :up_lcn, :up_tvg)
ON CONFLICT (id) DO UPDATE SET present = 1, url = excluded.url, extra = excluded.extra,
    up_name = excluded.up_name, up_icon = excluded.up_icon, up_lcn = excluded.up_lcn, up_tvg = excluded.up_tvg
"""
_GROUPS = "LEFT JOIN groups g ON g.name = c.grp"
_PLAYER_ORDER = "ORDER BY g.position IS NULL, g.position, c.position, c.id"


@contextmanager
def connect():
    con = sqlite3.connect(DB, timeout=30)
    con.row_factory = sqlite3.Row
    try:
        with con:  # commit, or roll back on error
            yield con
    finally:
        con.close()


def init():
    DATA.mkdir(parents=True, exist_ok=True)
    fresh = not DB.exists()
    with connect() as con:
        if any(column[1] == "xml" for column in con.execute("PRAGMA table_info(channels)")):
            con.executescript(MIGRATE_V1)
        con.executescript(SCHEMA)
        _ensure_groups(con, [r[0] for r in con.execute("SELECT grp FROM channels ORDER BY position")])
    if fresh:  # feeds are key-protected out of the box, so ship one working key
        add_token("default")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --- settings -------------------------------------------------------------

def get(key):
    with connect() as con:
        row = con.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return json.loads(row[0]) if row else DEFAULTS[key]


def put(key, value):
    with connect() as con:
        con.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", (key, json.dumps(value)))


# --- channels -------------------------------------------------------------

def import_channels(rows, playlist):
    """Refresh upstream data for known channels; add unseen ones to the end of their group, new groups last.

    A new channel starts disabled only if its whole group is currently disabled,
    so switching a group off keeps hiding channels that show up in it later.
    """
    with connect() as con:
        # Rows belong to one mode: streams from a playlist, or guide-only channels. Drop the other kind.
        con.execute("DELETE FROM channels WHERE (url IS NULL) = ?", (playlist,))
        con.execute("UPDATE channels SET present = 0")
        last = con.execute("SELECT COALESCE(MAX(position), -1) FROM channels").fetchone()[0]
        con.executemany(_UPSERT, [{**row, "position": last + n} for n, row in enumerate(rows, 1)])
        _ensure_groups(con, [row["grp"] for row in rows])


def channels():
    """Every known channel in player order, for the editor."""
    with connect() as con:
        rows = con.execute(
            "SELECT c.id, c.enabled, c.present, c.grp, c.url IS NOT NULL AS stream,"
            " c.up_name, c.up_icon, c.up_lcn, c.up_tvg, c.name, c.icon, c.lcn, c.tvg"
            f" FROM channels c {_GROUPS} {_PLAYER_ORDER}"
        )
        return [dict(r) for r in rows]


def layout():
    """The channels to publish, in player order, each with its matching guide channel if there is one."""
    with connect() as con:
        rows = con.execute(
            "SELECT c.grp, c.url, c.extra, c.name, c.icon, c.lcn, e.xml,"
            " COALESCE(c.tvg, c.up_tvg, '') AS tvg, COALESCE(c.name, c.up_name, '') AS shown_name,"
            " COALESCE(c.icon, c.up_icon, '') AS shown_icon, COALESCE(c.lcn, c.up_lcn, '') AS shown_lcn"
            " FROM channels c LEFT JOIN epg_channels e ON e.id = COALESCE(c.tvg, c.up_tvg)"
            f" {_GROUPS} WHERE c.enabled AND c.present {_PLAYER_ORDER}"
        )
        return [dict(r) for r in rows]


def update_channels(ids, fields):
    """Set the same column values on many channels at once."""
    if not fields or not fields.keys() <= EDITABLE:  # column names are interpolated below
        raise ValueError(f"editable fields are {sorted(EDITABLE)}")
    sets = ", ".join(f"{k} = ?" for k in fields)
    with connect() as con:
        con.executemany(f"UPDATE channels SET {sets} WHERE id = ?", [(*fields.values(), i) for i in ids])
        if "grp" in fields:
            _ensure_groups(con, [fields["grp"]])


def set_order(ids):
    with connect() as con:
        con.executemany("UPDATE channels SET position = ? WHERE id = ?", list(enumerate(ids)))


# --- groups ---------------------------------------------------------------

def _ensure_groups(con, names):
    """Add any group not known yet to the end of the group order."""
    known = {r[0] for r in con.execute("SELECT name FROM groups")}
    last = con.execute("SELECT COALESCE(MAX(position), -1) FROM groups").fetchone()[0]
    new = [name for name in dict.fromkeys(names) if name not in known]
    con.executemany("INSERT INTO groups VALUES (?, ?)", [(name, last + n) for n, name in enumerate(new, 1)])


def groups():
    with connect() as con:
        return [r[0] for r in con.execute("SELECT name FROM groups ORDER BY position, name")]


def set_groups(names):
    """Replace the group order. Naming a new group creates it; one left out is removed, unless it still has channels."""
    with connect() as con:
        current = [r[0] for r in con.execute("SELECT name FROM groups ORDER BY position, name")]
        in_use = {r[0] for r in con.execute("SELECT DISTINCT grp FROM channels")}
        order = dict.fromkeys([*names, *(name for name in current if name in in_use)])
        con.execute("DELETE FROM groups")
        con.executemany("INSERT INTO groups VALUES (?, ?)", [(name, n) for n, name in enumerate(order)])


def rename_group(old, new):
    """Rename a group, or fold it into `new` if that group already exists."""
    with connect() as con:
        con.execute("UPDATE channels SET grp = ? WHERE grp = ?", (new, old))
        if con.execute("SELECT 1 FROM groups WHERE name = ?", (new,)).fetchone():
            con.execute("DELETE FROM groups WHERE name = ?", (old,))
        else:
            con.execute("UPDATE groups SET name = ? WHERE name = ?", (new, old))


# --- upstream guide channels ----------------------------------------------

def set_epg_channels(chans):
    with connect() as con:
        con.execute("DELETE FROM epg_channels")
        con.executemany("INSERT OR REPLACE INTO epg_channels VALUES (:id, :name, :xml)", chans)


def epg_channels():
    """(id, display name) of every channel the upstream guide has data for."""
    with connect() as con:
        return [tuple(r) for r in con.execute("SELECT id, name FROM epg_channels ORDER BY id")]


# --- access tokens --------------------------------------------------------

def tokens():
    with connect() as con:
        return [dict(r) for r in con.execute("SELECT token, label, created FROM tokens ORDER BY created, label")]


def add_token(label):
    with connect() as con:
        con.execute("INSERT INTO tokens VALUES (?, ?, ?)", (secrets.token_urlsafe(16), label, now()))


def delete_token(token):
    with connect() as con:
        con.execute("DELETE FROM tokens WHERE token = ?", (token,))


def token_exists(token):
    with connect() as con:
        return con.execute("SELECT 1 FROM tokens WHERE token = ?", (token,)).fetchone() is not None
