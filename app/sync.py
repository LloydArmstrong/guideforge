"""Orchestration: a sync fetches upstream, brings the channel list up to date, and publishes.

A sync runs when the operator presses Sync now and on the schedule. Nothing else fetches or
publishes: editing the line-up only marks it as having changes waiting.
"""
import logging
import threading
from contextlib import contextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from . import db, ingest, m3u, publish, transform, xmltv, xtream

log = logging.getLogger(__name__)
scheduler = BackgroundScheduler()
# What a sync is doing right now, in words the edition line prints after "Stop press:", and the bytes
# of the download in hand as (done, total). In-process, which is why the app runs a single worker.
state = {"running": None, "progress": None}
_lock = threading.Lock()  # one sync at a time


def _status(**changes):
    db.put("status", {**db.get("status"), **changes})


def _step(doing):
    state.update(running=doing, progress=None)


def _progress(done, total):
    state["progress"] = (done, total)


@contextmanager
def _job(name):
    with _lock:
        _step(f"starting the {name}")
        try:
            yield
            _status(error=None)
        except Exception as e:  # a failed run keeps what was published before
            log.exception("%s failed", name)
            _status(error=f"{name} failed: {e}")
        finally:
            _step(None)


def mark_dirty():
    """Record that the line-up has edits the published files do not carry yet."""
    db.put("dirty", True)


def _guide_row(channel):
    """With no playlist, the guide's own channels are the line-up."""
    return {
        "id": channel["id"],
        "grp": transform.guess_group(channel["id"], channel["name"]),
        "url": None,
        "extra": None,
        "up_name": channel["name"],
        "up_icon": channel["icon"],
        "up_lcn": channel["lcn"],
        "up_tvg": channel["id"],
    }


def sources():
    """What is configured: (provider login or None, playlist address, guide address)."""
    login = (xtream.server_root(db.get("xtream_url")), db.get("xtream_user"), db.get("xtream_pass"))
    return (login if all(login) else None), db.get("playlist_url"), db.get("upstream_url")


def _refresh(login, playlist_url, guide_url):
    """Download the configured sources and bring the channel list up to date."""
    guide = []
    if guide_url:
        _step("downloading the guide")
        tmp = db.UPSTREAM.with_suffix(".part")
        size = ingest.fetch(guide_url, tmp, _progress)
        _step("reading the guide")
        guide = list(xmltv.read_channels(tmp))
        if not guide:  # an error page or empty file must not replace a good cache
            raise ValueError("the guide address returned no <channel> elements, is it XMLTV?")
        tmp.replace(db.UPSTREAM)
        db.set_epg_channels(guide)
        _status(upstream_bytes=size)
    if login:
        _step("reading your channels from the provider")
        entries = list(xtream.read_channels(*login))
        if not entries:
            raise ValueError("the provider lists no live channels for this login")
        db.import_channels(entries, playlist=True)
    elif playlist_url:
        _step("downloading the playlist from your provider")
        tmp = db.PLAYLIST.with_suffix(".download")
        try:
            ingest.fetch(playlist_url, tmp, _progress)
            entries = list(m3u.read_entries(tmp))
        finally:
            tmp.unlink(missing_ok=True)  # it holds the provider login; the database keeps what is needed
        if not entries:
            raise ValueError("the playlist address returned no channels, is it an M3U playlist?")
        db.import_channels(entries, playlist=True)
    else:
        db.import_channels([_guide_row(c) for c in guide], playlist=False)
    _status(last_sync=db.now())


def _build():
    _step("publishing the new edition")
    db.put("dirty", False)  # edits landing from here on wait for the next sync
    rows = db.layout()
    guide = {}  # guide channels in player order; the first channel using an id sets its overrides
    for row in rows:
        if row["xml"] and row["tvg"] not in guide:
            guide[row["tvg"]] = {**row, "id": row["tvg"]}
    programmes = 0
    if db.UPSTREAM.exists():
        programmes = transform.build(db.UPSTREAM, db.OUTPUT, list(guide.values()))["programmes"]
    streams = [row for row in rows if row["url"]]
    if streams:
        transform.build_playlist(db.PLAYLIST, streams)
    else:
        db.PLAYLIST.unlink(missing_ok=True)
    _status(
        built_at=db.now(),
        output_bytes=db.OUTPUT.stat().st_size if db.OUTPUT.exists() else None,
        channels=len(rows),
        guide_channels=len(guide),
        programmes=programmes,
    )
    log.info("published %d channels, %d with guide data, %d programmes", len(rows), len(guide), programmes)
    if publish.enabled() and db.OUTPUT.exists():
        _step("uploading the guide to R2")
        try:
            publish.upload(db.OUTPUT)
        except Exception as e:  # the guide itself is published; say which half went wrong
            raise RuntimeError(f"R2 upload failed: {e}") from e


def sync():
    """Fetch upstream, pick up new channels, and publish the playlist and guide."""
    with _job("sync"):
        configured = sources()
        if not any(configured):
            return
        try:
            _refresh(*configured)
        except Exception:
            if db.get("dirty"):  # a failed download must not hold the operator's edits back
                _build()
            raise
        _build()


def sync_now():
    # Said before the thread starts, so the editor's very next look already finds a sync under way.
    state["running"] = state["running"] or "starting the sync"
    threading.Thread(target=sync, daemon=True).start()


def trigger(spec):
    """'24' means every 24 hours; anything else is a 5-field crontab expression."""
    spec = spec.strip()
    if spec.replace(".", "", 1).isdigit():
        hours = float(spec)
        if hours < 0.25:
            raise ValueError("the shortest interval is 0.25 hours")
        return IntervalTrigger(hours=hours)
    return CronTrigger.from_crontab(spec)


def apply_schedule():
    scheduler.add_job(
        sync, trigger(db.get("schedule")), id="sync", replace_existing=True, misfire_grace_time=None, coalesce=True
    )


def next_sync():
    job = scheduler.get_job("sync")
    when = getattr(job, "next_run_time", None)
    return when.isoformat(timespec="seconds") if when else None


def start():
    apply_schedule()
    scheduler.start()
