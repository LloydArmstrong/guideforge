"""Management API behind HTTP Basic auth, used by the web UI."""
import logging
import os
import secrets
from typing import Annotated
from urllib.parse import urlsplit

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field

from . import db, publish, sync, xtream

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
    xtream_url: str
    xtream_user: str
    xtream_pass: str
    playlist_url: str
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
    tvg: str | None = None


class GroupRename(BaseModel):
    old: str
    new: str = Field(min_length=1, max_length=80)


@router.get("/state")
def state():
    return {
        "settings": {key: db.get(key) for key in Settings.model_fields},
        "status": db.get("status"),
        "running": sync.state["running"],
        "progress": sync.state["progress"],
        "dirty": db.get("dirty"),
        "playlist": db.PLAYLIST.exists(),
        "guide": db.OUTPUT.exists(),
        "next_sync": sync.next_sync(),
        "tokens": db.tokens(),
        "r2_url": publish.PUBLIC_URL if publish.enabled() else "",
    }


@router.put("/settings")
def save_settings(settings: Settings):
    new = {
        "xtream_url": xtream.server_root(settings.xtream_url),
        "xtream_user": settings.xtream_user.strip(),
        "xtream_pass": settings.xtream_pass.strip(),
        "playlist_url": settings.playlist_url.strip(),
        "upstream_url": settings.upstream_url.strip(),
        "schedule": settings.schedule.strip(),
        "public_url": settings.public_url.strip().rstrip("/"),
        "public_access": settings.public_access,
    }
    for url in (new["playlist_url"], new["upstream_url"], new["public_url"]):
        if url and urlsplit(url).scheme not in ("http", "https"):
            raise HTTPException(400, "Addresses must start with http:// or https://")
    login = [settings.xtream_url.strip(), new["xtream_user"], new["xtream_pass"]]
    if any(login) and not (all(login) and new["xtream_url"]):
        raise HTTPException(400, "A provider login needs all three: server address, username and password")
    try:
        sync.trigger(new["schedule"])
    except ValueError as e:
        raise HTTPException(400, f"Invalid schedule: {e}")
    for key, value in new.items():
        db.put(key, value)
    sync.apply_schedule()  # a new address is fetched at the next sync, not now
    return new


@router.post("/sync", status_code=202)
def sync_now():
    if not any(sync.sources()):
        raise HTTPException(400, "Add your provider login or a guide address under Source first")
    sync.sync_now()
    return {}


@router.get("/channels")
def channels():
    return {"groups": db.groups(), "channels": db.channels(), "guide": db.epg_channels()}


@router.patch("/channels")
def patch_channels(patch: ChannelPatch):
    """One endpoint for single edits and bulk actions: the same values go to every id."""
    fields = patch.model_dump(exclude={"ids"}, exclude_none=True)
    if not fields:
        raise HTTPException(400, "Nothing to change")
    for key in fields.keys() & {"grp", "name", "icon", "lcn", "tvg"}:
        fields[key] = fields[key].strip()
    for key in fields.keys() & {"name", "icon", "lcn", "tvg"}:
        fields[key] = fields[key] or None  # clearing an override falls back to upstream
    db.update_channels(patch.ids, fields)
    sync.mark_dirty()
    return {}


@router.put("/channels/order")
def reorder(ids: list[str]):
    db.set_order(ids)
    sync.mark_dirty()
    return {}


@router.put("/groups")
def set_groups(names: list[str]):
    """The whole group order. Naming a new group creates it; an empty group left out is removed."""
    db.set_groups([name.strip() for name in names])
    sync.mark_dirty()
    return db.groups()


@router.post("/groups/rename")
def rename_group(rename: GroupRename):
    new = rename.new.strip()
    if not new:
        raise HTTPException(400, "A group needs a name")
    db.rename_group(rename.old, new)
    sync.mark_dirty()
    return db.groups()


@router.post("/tokens")
def add_token(label: Annotated[str, Body(embed=True, min_length=1, max_length=80)]):
    db.add_token(label.strip())
    return db.tokens()


@router.delete("/tokens/{token}")
def delete_token(token: str):
    db.delete_token(token)
    return db.tokens()
