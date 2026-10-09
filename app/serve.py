"""Public delivery: the guide endpoints remote players fetch."""
import gzip
from email.utils import formatdate

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, Response, StreamingResponse

from . import db

router = APIRouter()
METHODS = ["GET", "HEAD"]  # some players probe with HEAD first


def _gunzip(path):
    with gzip.open(path, "rb") as f:
        while chunk := f.read(1 << 16):
            yield chunk


def _feed(request, key, gz):
    public = db.get("public_access")
    if not public and not (key and db.token_exists(key)):
        raise HTTPException(403, "Invalid or missing key")
    if not db.OUTPUT.exists():
        raise HTTPException(503, "Guide not built yet", headers={"Retry-After": "60"})

    stat = db.OUTPUT.stat()
    # Weak validator: /epg.xml is the same guide whether sent gzip-encoded or not.
    tag = f'"{stat.st_mtime_ns:x}-{stat.st_size:x}"'
    modified = formatdate(stat.st_mtime, usegmt=True)
    headers = {
        "ETag": f"W/{tag}",
        "Last-Modified": modified,
        # Keyed URLs revalidate every time, so a revoked key stops working even behind a CDN.
        "Cache-Control": "public, max-age=300" if public else "private, no-cache",
        "Access-Control-Allow-Origin": "*",
        "Vary": "Accept-Encoding",
    }
    if_none_match = request.headers.get("if-none-match")
    if if_none_match is not None:  # takes precedence over If-Modified-Since
        unchanged = tag in if_none_match or if_none_match.strip() == "*"
    else:
        unchanged = request.headers.get("if-modified-since") == modified
    if unchanged:
        return Response(status_code=304, headers=headers)

    if gz:  # the .gz file itself: the player gunzips it
        return FileResponse(db.OUTPUT, media_type="application/x-gzip", headers=headers)
    if "gzip" in request.headers.get("accept-encoding", ""):  # same bytes as transport compression
        return FileResponse(db.OUTPUT, media_type="application/xml", headers={**headers, "Content-Encoding": "gzip"})
    return StreamingResponse(_gunzip(db.OUTPUT), media_type="application/xml", headers=headers)


@router.api_route("/epg.xml", methods=METHODS)
@router.api_route("/u/{slug}/epg.xml", methods=METHODS)
def epg_xml(request: Request, slug: str | None = None, key: str | None = None):
    return _feed(request, slug or key, gz=False)


@router.api_route("/epg.xml.gz", methods=METHODS)
@router.api_route("/u/{slug}/epg.xml.gz", methods=METHODS)
def epg_xml_gz(request: Request, slug: str | None = None, key: str | None = None):
    return _feed(request, slug or key, gz=True)
