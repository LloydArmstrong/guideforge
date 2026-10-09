"""SQLite persistence: channel layout, settings and access tokens."""
import json
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DATA = Path(os.environ.get("DATA_DIR", "data"))
DB = DATA / "guideforge.db"
UPSTREAM = DATA / "upstream.cache"  # last good upstream download, exactly as received
OUTPUT = DATA / "epg.xml.gz"  # the published guide

SCHEMA = """
CREATE TABLE IF NOT EXISTS channels (
    id       TEXT PRIMARY KEY,            -- XMLTV channel id; never rewritten, players match on it
    position INTEGER NOT NULL,
    enabled  INTEGER NOT NULL DEFAULT 1,
    present  INTEGER NOT NULL DEFAULT 1,  -- seen in the latest upstream sync
    grp      TEXT NOT NULL DEFAULT '',
    xml      TEXT NOT NULL,               -- upstream <channel> element, as last seen
    up_name  TEXT, up_icon TEXT, up_lcn TEXT,
    name     TEXT, icon TEXT, lcn TEXT    -- overrides; NULL means "use upstream"
);
CREATE INDEX IF NOT EXISTS channels_grp ON channels (grp, enabled);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS tokens (token TEXT PRIMARY KEY, label TEXT NOT NULL, created TEXT NOT NULL);
"""

# Env vars only seed first-run defaults; values saved from the UI win.
DEFAULTS = {
    "upstream_url": os.environ.get("UPSTREAM_URL", ""),
    "schedule": os.environ.get("SYNC_SCHEDULE", "6"),
    "public_url": os.environ.get("PUBLIC_URL", "").rstrip("/"),
    "public_access": False,
    "status": {},
}
EDITABLE = {"enabled", "grp", "name", "icon", "lcn"}


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
        con.executescript(SCHEMA)
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


# --- channel layout -------------------------------------------------------

def import_channels(chans):
    """Refresh upstream data for known channels and append unseen ones to the end of the guide.

    A new channel starts disabled only if its whole group is currently disabled,
    so switching a group off keeps hiding channels that show up in it later.
    """
    with connect() as con:
        con.execute("UPDATE channels SET present = 0")
        last = con.execute("SELECT COALESCE(MAX(position), -1) FROM channels").fetchone()[0]
        con.executemany(
            """INSERT INTO channels (id, position, enabled, grp, xml, up_name, up_icon, up_lcn)
               VALUES (:id, :position, COALESCE((SELECT MAX(enabled) FROM channels WHERE grp = :grp), 1),
                       :grp, :xml, :name, :icon, :lcn)
               ON CONFLICT (id) DO UPDATE SET present = 1, xml = excluded.xml,
                   up_name = excluded.up_name, up_icon = excluded.up_icon, up_lcn = excluded.up_lcn""",
            [{**c, "position": last + n} for n, c in enumerate(chans, 1)],
        )


def channels():
    """Every known channel in guide order, for the editor."""
    with connect() as con:
        rows = con.execute(
            "SELECT id, enabled, present, grp, up_name, up_icon, up_lcn, name, icon, lcn"
            " FROM channels ORDER BY position, id"
        )
        return [dict(r) for r in rows]


def layout():
    """The channels to publish, in guide order."""
    with connect() as con:
        rows = con.execute(
            "SELECT id, xml, name, icon, lcn FROM channels WHERE enabled AND present ORDER BY position, id"
        )
        return [dict(r) for r in rows]


def update_channels(ids, fields):
    """Set the same column values on many channels at once."""
    if not fields or not fields.keys() <= EDITABLE:  # column names are interpolated below
        raise ValueError(f"editable fields are {sorted(EDITABLE)}")
    sets = ", ".join(f"{k} = ?" for k in fields)
    with connect() as con:
        con.executemany(f"UPDATE channels SET {sets} WHERE id = ?", [(*fields.values(), i) for i in ids])


def set_order(ids):
    with connect() as con:
        con.executemany("UPDATE channels SET position = ? WHERE id = ?", list(enumerate(ids)))


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
