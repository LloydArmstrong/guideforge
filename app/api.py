"""Management API behind HTTP Basic auth, used by the web UI."""
import logging
import os
import secrets
from typing import Annotated
from urllib.parse import urlsplit

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

from . import db, publish, sync

log = logging.getLogger(__name__)

PASSWORD = os.environ.get("ADMIN_PASSWORD") or secrets.token_urlsafe(12)
if not os.environ.get("ADMIN_PASSWORD"):  # never run with the editor open
    log.warning("ADMIN_PASSWORD is not set. Generated one for this run: %s", PASSWORD)


def admin(request: Request, credentials: Annotated[HTTPBasicCredentials, Depends(HTTPBasic())]):
    """Any username, the admin password."""
    if not secrets.compare_digest(credentials.password.encode(), PASSWORD.encode()):
        raise HTTPException(401, "Wrong password", headers={"WWW-Authenticate": "Basic"})
    # Browsers attach Basic credentials to cross-site requests too; refuse those for writes.
    if request.method != "GET" and request.headers.get("sec-fetch-site", "same-origin") not in ("same-origin", "none"):
        raise HTTPException(403, "Cross-site request blocked")


router = APIRouter(prefix="/api", dependencies=[Depends(admin)])


class Settings(BaseModel):
    upstream_url: str
    schedule: str
    public_url: str
    public_access: bool


class ChannelPatch(BaseModel):
    ids: list[str]
    enabled: bool | None = None
    grp: str | None = None
    name: str | None = None
    icon: str | None = None
    lcn: str | None = None


@router.get("/state")
def state():
    return {
        "settings": {key: db.get(key) for key in Settings.model_fields},
        "status": db.get("status"),
        **sync.state,
        "next_sync": sync.next_sync(),
        "tokens": db.tokens(),
        "r2_url": publish.PUBLIC_URL if publish.enabled() else "",
    }


@router.put("/settings")
def save_settings(settings: Settings):
    new = {
        "upstream_url": settings.upstream_url.strip(),
        "schedule": settings.schedule.strip(),
        "public_url": settings.public_url.strip().rstrip("/"),
        "public_access": settings.public_access,
    }
    for url in (new["upstream_url"], new["public_url"]):
        if url and urlsplit(url).scheme not in ("http", "https"):
            raise HTTPException(400, "URLs must start with http:// or https://")
    try:
        sync.trigger(new["schedule"])
    except ValueError as e:
        raise HTTPException(400, f"Invalid schedule: {e}")
    source_changed = new["upstream_url"] != db.get("upstream_url")
    for key, value in new.items():
        db.put(key, value)
    sync.apply_schedule()
    if source_changed:
        sync.sync_now()
    return new


@router.post("/sync", status_code=202)
def sync_now():
    if not db.get("upstream_url"):
        raise HTTPException(400, "Set an upstream URL first")
    sync.sync_now()
    return {}


@router.get("/channels")
def channels():
    return db.channels()


@router.patch("/channels")
def patch_channels(patch: ChannelPatch):
    """One endpoint for single edits and bulk actions: the same values go to every id."""
    fields = patch.model_dump(exclude={"ids"}, exclude_none=True)
    if not fields:
        raise HTTPException(400, "Nothing to change")
    for key in fields.keys() & {"grp", "name", "icon", "lcn"}:
        fields[key] = fields[key].strip()
    for key in fields.keys() & {"name", "icon", "lcn"}:
        fields[key] = fields[key] or None  # clearing an override falls back to upstream
    db.update_channels(patch.ids, fields)
    sync.schedule_rebuild()
    return {}


@router.put("/channels/order")
def reorder(ids: list[str]):
    db.set_order(ids)
    sync.schedule_rebuild()
    return {}


@router.post("/tokens")
def add_token(label: Annotated[str, Body(embed=True, min_length=1, max_length=80)]):
    db.add_token(label.strip())
    return db.tokens()


@router.delete("/tokens/{token}")
def delete_token(token: str):
    db.delete_token(token)
    return db.tokens()
