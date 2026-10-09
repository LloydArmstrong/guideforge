# GuideForge

A self-hosted editor for XMLTV TV guides. It pulls one upstream guide on a schedule, applies your line-up (order, visibility, names, channel numbers, logos) and serves the result, gzip-compressed, to as many remote IPTV players as you like. Each viewer gets their own revocable URL.

## Quick start

```sh
cp .env.example .env        # set ADMIN_PASSWORD
docker compose up -d
```

Open `http://<host>:8000`, sign in (any username, the admin password), and paste your provider's XMLTV address under **Source**. The first sync lists every channel in upstream order; from then on your line-up is re-applied to every sync and channels you have never seen are added to the end.

Edits publish themselves a few seconds after you stop making them. There is no save button.

## Guide URLs

| URL | What a player gets |
| --- | --- |
| `/u/<key>/epg.xml.gz` | The gzipped guide. Use this one: the URL ends in `.gz`, which some players need. |
| `/u/<key>/epg.xml` | XML, sent with `Content-Encoding: gzip` when the player accepts it. |
| `/epg.xml.gz?key=<key>`, `/epg.xml?key=<key>` | The same, with the key as a query parameter. |
| `/epg.xml.gz`, `/epg.xml` | Only when "Let anyone with the address fetch the guide" is on. |

Keys are created and revoked under **Viewers**, which also has a copy button for each address. Responses carry `ETag`, `Last-Modified` and `Access-Control-Allow-Origin: *`, and answer conditional requests with `304`.

## Reaching it from the internet

The app listens on port 8000 and serves both the editor and the feeds. Three ways to publish the feeds:

- **Your own reverse proxy.** Proxy to `guideforge:8000`. To keep the editor off the internet, forward only `/epg.xml*` and `/u/`.
- **Bundled nginx** (`docker compose --profile nginx up -d`). Listens on port 80 and forwards only the feed paths; see `nginx.conf`. Terminate TLS in front of it.
- **Cloudflare Tunnel** (`docker compose --profile tunnel up -d`, with `TUNNEL_TOKEN` in `.env`). Point the tunnel's public hostname at `http://nginx:80` for feeds only, or `http://guideforge:8000` for feeds and editor.

Set **Public address of this server** under Source so the Viewers page writes addresses with your hostname.

**Cloudflare R2 mirror (optional).** Set the `R2_*` variables and every published guide is also uploaded to the bucket as `epg.xml.gz` and `epg.xml`. A public bucket URL cannot check keys, so anyone with that address can read the guide.

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `ADMIN_PASSWORD` | random, printed at start | Password for the editor and its API. |
| `UPSTREAM_URL` | empty | First-run upstream address. Saved settings win afterwards. |
| `SYNC_SCHEDULE` | `6` | Hours between syncs, or a five-field cron expression. |
| `PUBLIC_URL` | empty | First-run public address of this server. |
| `TZ` | `UTC` | Time zone for cron schedules. |
| `DATA_DIR` | `/data` | SQLite database, upstream cache and the published guide. |
| `R2_ENDPOINT`, `R2_BUCKET`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_PUBLIC_URL` | empty | Optional R2 mirror. |

## Groups

XMLTV has no notion of groups, so each new channel gets a guessed one: `UK: BBC One` becomes `UK`, and an id like `bbc1.uk` becomes `UK`. Groups are editable per channel. A channel that arrives in a group you have switched off entirely stays off.

## How it is put together

| Module | Job |
| --- | --- |
| `app/ingest.py` | Stream the upstream guide to disk. |
| `app/xmltv.py` | Streaming XMLTV parser; memory stays flat whatever the guide size. |
| `app/transform.py` | Apply order, visibility and overrides; write the gzipped guide. |
| `app/db.py` | SQLite: channel layout, settings, viewer keys. |
| `app/sync.py` | Scheduling and orchestration: fetch, import, build, publish. |
| `app/publish.py` | Optional R2 upload. |
| `app/serve.py` | Public feed endpoints: keys, gzip, caching headers. |
| `app/api.py` | Password-protected management API. |
| `app/static/index.html` | The editor (one file, no build step). |

A 110 MB guide (2,500 channels, 275,000 programmes) syncs in about 3 seconds and stays under 50 MB of memory on a laptop.

The app runs one worker by design: the scheduler and the sync lock live in the process.

## Development

```sh
python -m venv .venv && .venv/bin/pip install -r requirements.txt httpx
ADMIN_PASSWORD=dev .venv/bin/uvicorn app.main:app --reload
.venv/bin/python tests/test_guideforge.py
```
