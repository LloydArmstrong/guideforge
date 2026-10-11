# GuideForge

A self-hosted editor for what your IPTV players show: which channels, in which groups, in what order, with which TV guide. It pulls your provider's playlist and an XMLTV guide, applies your line-up, and serves an edited playlist and a matching gzip-compressed guide to as many remote players as you like. Each viewer gets their own revocable addresses.

## Why it serves the playlist

Players such as TiviMate take channels, their order and their groups from the **playlist**, never from the guide. So GuideForge sits between your provider and your players for both:

```
provider (Xtream login)  ─┐                    ┌─  /u/<key>/playlist.m3u  ─┐
                          ├─  GuideForge  ─────┤                           ├─  TiviMate
EPG supplier (XMLTV)     ─┘   your line-up     └─  /u/<key>/epg.xml.gz    ─┘
```

Video never passes through GuideForge: the playlist it serves still points at your provider's streams.

## Quick start

```sh
cp .env.example .env        # set ADMIN_PASSWORD
docker compose up -d
```

1. Open `http://<host>:8000` and sign in (any username, the admin password).
2. Under **Source**, enter your provider's Xtream Codes login (server, username, password) and the guide address from your EPG supplier, and save.
   - If your provider gave you an M3U link instead of a login, open "My provider gave me an M3U link" and paste it there.
3. Press **Sync now**. Your channels appear under **Line-up** in the provider's groups.
4. Arrange them, then press **Sync now** again to publish.
5. Under **Viewers**, copy a playlist address. In TiviMate choose Add playlist, then **M3U playlist**, and paste it. Do not enter your provider's Xtream login in TiviMate: that would bypass GuideForge and show the provider's own groups. The playlist names that viewer's guide address, so the TV guide should follow on its own; if your player does not pick it up, add the guide address as well.

## When things are fetched and published

Only on a sync, and a sync runs only when you press **Sync now** or on the schedule (every day at 04:00 unless you change it). Editing the line-up saves your changes and marks them as unpublished; players keep getting the previous edition until the next sync.

If a download fails during a sync, your waiting edits are still published from the last good download, and the error is shown.

## Arranging the line-up

- **Groups** are listed in the order players show them. Drag a group to move it, add new ones, rename or merge them, and remove empty ones.
- **Big providers.** Type in "Find a group" to narrow the index, or tick "Only groups that are on". "Turn on" and "Turn off" act on every group currently listed, after asking. A quick way to start from a provider with hundreds of groups: Turn off with nothing typed, then find the ones you want (for example `UK|`) and Turn on.
- **Channels** are shown one group at a time; click a group's name to read it. They move by dragging the grip, by typing a position into the number box, or with the arrow keys on the grip. Dropping a channel on a group in the index moves it into that group. Searching looks across every group and shows the first 400 matches.
- A tick turns a channel, or a whole group, on or off. A channel that later appears in a group you switched off entirely stays off.
- Display name, channel number (LCN) and logo can be overridden per channel. Clear a field to go back to the provider's value.
- **Guide ID** is the guide channel a stream takes its programmes from. Ids are matched whatever their letter case. A stream the guide cannot match is shown in red; pick the right guide channel from the list to fix it.
- New channels from the provider join the end of their group; new provider groups are added last.

## Addresses

| URL | What a player gets |
| --- | --- |
| `/u/<key>/playlist.m3u` | The edited playlist. Its first line carries the viewer's guide address. |
| `/u/<key>/epg.xml.gz` | The gzipped guide, trimmed to the channels you publish. |
| `/u/<key>/epg.xml` | The guide as XML, sent with `Content-Encoding: gzip` when the player accepts it. |
| `/playlist.m3u?key=<key>`, `/epg.xml.gz?key=<key>` | The same, with the key as a query parameter. |
| The same paths with no key | Only when keyless access is switched on under Source. |

Responses carry `ETag`, `Last-Modified` and `Access-Control-Allow-Origin: *`, and answer conditional requests with `304`.

## Things to know

- **Everyone shares your provider login.** The playlist contains your provider's stream addresses, login included. Give it only to people you would give that login to; the provider's connection limit applies across all of them.
- **Live channels only.** Film and series entries in the provider playlist are left out. An M3U playlist also gives TiviMate no film or series sections; if you want those, keep the Xtream Codes login as a second playlist in TiviMate.
- **Without a playlist address** GuideForge edits the guide on its own, which trims and renames guide data but cannot change what a player lists.
- **Your line-up survives a password change.** Channels are tracked by their Xtream stream number, so a new provider password, or a switch from an M3U link to the login, does not reset it.

## Reaching it from the internet

The app listens on port 8000 and serves both the editor and the feeds.

- **Your own reverse proxy.** Proxy to `guideforge:8000`. To keep the editor off the internet, forward only `/playlist.m3u`, `/epg.xml*` and `/u/`.
- **Bundled nginx** (`docker compose --profile nginx up -d`). Listens on port 80 and forwards only the feed paths; see `nginx.conf`. Terminate TLS in front of it.
- **Cloudflare Tunnel** (`docker compose --profile tunnel up -d`, with `TUNNEL_TOKEN` in `.env`). Point the tunnel's public hostname at `http://nginx:80` for feeds only, or `http://guideforge:8000` for feeds and editor.

Set **Public address of this server** under Source so viewer addresses, and the guide address inside each playlist, use your hostname.

**Cloudflare R2 mirror (optional).** Set the `R2_*` variables and every published guide is also uploaded to the bucket as `epg.xml.gz` and `epg.xml`. The playlist is never mirrored. A public bucket URL cannot check keys.

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `ADMIN_PASSWORD` | random, printed at start | Password for the editor and its API. |
| `XTREAM_URL`, `XTREAM_USER`, `XTREAM_PASS` | empty | First-run provider login. Saved settings win afterwards. |
| `PLAYLIST_URL` | empty | First-run M3U address, for a provider with no login. |
| `UPSTREAM_URL` | empty | First-run guide address. |
| `SYNC_SCHEDULE` | `0 4 * * *` | A five-field cron expression, or hours between syncs. |
| `PUBLIC_URL` | empty | First-run public address of this server. |
| `TZ` | `UTC` | Time zone for cron schedules. |
| `DATA_DIR` | `/data` | SQLite database, guide cache and the published files. |
| `R2_ENDPOINT`, `R2_BUCKET`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_PUBLIC_URL` | empty | Optional R2 mirror of the guide. |

## How it is put together

| Module | Job |
| --- | --- |
| `app/ingest.py` | Stream a download to disk. |
| `app/xtream.py` | Read live channels and groups through the provider's Xtream Codes API. |
| `app/m3u.py` | Streaming M3U parser, for providers that give a playlist link instead. |
| `app/xmltv.py` | Streaming XMLTV parser; memory stays flat whatever the guide size. |
| `app/transform.py` | Apply the line-up; write the playlist and the gzipped guide. |
| `app/db.py` | SQLite: channels, groups, guide channels, settings, viewer keys. |
| `app/sync.py` | Scheduling and orchestration: fetch, import, publish. |
| `app/publish.py` | Optional R2 upload. |
| `app/serve.py` | Public feed endpoints: keys, gzip, caching headers. |
| `app/api.py` | Password-protected management API. |
| `app/static/index.html` | The editor (one file, no build step). |

The app runs one worker by design: the scheduler and the sync lock live in the process.

## Development

```sh
python -m venv .venv && .venv/bin/pip install -r requirements.txt httpx
ADMIN_PASSWORD=dev .venv/bin/uvicorn app.main:app --reload
.venv/bin/python tests/test_guideforge.py
```
