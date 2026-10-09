"""Orchestration: scheduled sync (fetch -> import -> build -> publish) and rebuilds after edits."""
import logging
import threading
from contextlib import contextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from . import db, ingest, publish, transform, xmltv

log = logging.getLogger(__name__)
scheduler = BackgroundScheduler()
state = {"running": None, "dirty": False}  # in-process, which is why the app runs a single worker
_lock = threading.Lock()  # one sync or build at a time
_timer = None


def _status(**changes):
    db.put("status", {**db.get("status"), **changes})


@contextmanager
def _job(name):
    with _lock:
        state["running"] = name
        try:
            yield
            _status(error=None)
        except Exception as e:  # a failed run keeps the previously published guide
            log.exception("%s failed", name)
            _status(error=f"{name} failed: {e}")
        finally:
            state["running"] = None


def _build():
    state["dirty"] = False  # edits landing from here on need another build
    stats = transform.build(db.UPSTREAM, db.OUTPUT, db.layout())
    _status(built_at=db.now(), output_bytes=db.OUTPUT.stat().st_size, **stats)
    log.info("published %(channels)d channels, %(programmes)d programmes", stats)
    if publish.enabled():
        try:
            publish.upload(db.OUTPUT)
        except Exception as e:  # the guide itself is published; say which half went wrong
            raise RuntimeError(f"R2 upload failed: {e}") from e


def sync():
    """Fetch upstream, pick up new channels, rebuild and publish."""
    url = db.get("upstream_url")
    if not url:
        return
    with _job("sync"):
        tmp = db.UPSTREAM.with_suffix(".part")
        size = ingest.fetch(url, tmp)
        chans = list(xmltv.read_channels(tmp))
        if not chans:  # an error page or empty file must not replace a good cache
            raise ValueError("upstream has no <channel> elements, is it an XMLTV guide?")
        tmp.replace(db.UPSTREAM)
        for c in chans:
            c["grp"] = transform.guess_group(c["id"], c["name"])
        db.import_channels(chans)
        _status(last_sync=db.now(), upstream_bytes=size)
        _build()


def rebuild():
    """Re-apply the layout to the cached upstream guide, without downloading it again."""
    if db.UPSTREAM.exists():
        with _job("build"):
            _build()


def schedule_rebuild(delay=3):
    """Debounce: a burst of edits (a drag, a bulk toggle) becomes one rebuild."""
    global _timer
    state["dirty"] = True
    if _timer:
        _timer.cancel()
    _timer = threading.Timer(delay, rebuild)
    _timer.daemon = True
    _timer.start()


def sync_now():
    threading.Thread(target=sync, daemon=True).start()


def trigger(spec):
    """'6' means every 6 hours; anything else is a 5-field crontab expression."""
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
    if not db.OUTPUT.exists():
        sync_now()
