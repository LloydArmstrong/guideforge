"""App assembly: public feed routes, the management API and the editor UI."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import api, db, serve, sync

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
STATIC = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app):
    db.init()
    sync.start()
    yield
    sync.scheduler.shutdown(wait=False)


# Internet-facing: no auto-generated API docs.
app = FastAPI(title="GuideForge", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.include_router(serve.router)
app.include_router(api.router)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", dependencies=[Depends(api.admin)])
def editor():
    return FileResponse(STATIC / "index.html")


@app.get("/healthz")
def healthz():
    return {"ok": True}
