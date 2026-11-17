# Per-viewer Provider Login Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let each viewer carry their own provider username and password, swapped into their playlist's stream addresses as it is served.

**Architecture:** The published playlist is still built once per sync with the operator's login. `serve.playlist` rewrites the username/password segments of every Xtream-shaped stream line when the requesting viewer has a login of their own. The login lives on the viewer's row in `tokens`.

**Tech Stack:** FastAPI, SQLite, one-file HTML editor (no build step).

**Spec:** `docs/superpowers/specs/2026-11-16-per-viewer-login-design.md`

## Global Constraints

- No new dependencies. Python 3.14, stdlib `re` and `urllib.parse.quote`.
- The editor stays one HTML file with no build step.
- A viewer with no login gets the operator's login, exactly as today.
- Sync, line-up and guide code are not touched.
- Work on branch `per-viewer-login`, cut from local `main` (do not pull: local `main` was rewritten and is waiting for a force-push).
- Tests run with `.venv/bin/python tests/test_guideforge.py` and must print `ok`.

## Review Focus

1. **A player holding the old playlist after a login change.** Players send `If-None-Match`; the ETag comes from the file's mtime and size, so without a fix they would get `304` and keep the old login. Saving a login must make the next fetch a `200`. Test in Task 1.
2. **Passwords with `/`, space, `@` or `%`.** They must be URL-quoted the way `xtream.py` does it, or the stream path breaks. Test in Task 1.
3. **Only one of username/password entered.** The API refuses it with `400`, the same as Source does. Test in Task 1.
4. **Both fields cleared.** The viewer goes back to the operator's login. Test in Task 1.
5. **An existing database.** `tokens` gains the two columns in place, and existing viewers keep working with no login. Test in Task 1.

---

### Task 1: Store, serve and edit a viewer's login (backend)

**Files:**
- Modify: `app/m3u.py` (`_XTREAM`, `stream_key`, new `with_login`)
- Modify: `app/db.py` (`SCHEMA` tokens table, `init`, `tokens`, new `set_token_login`, new `token_login`)
- Modify: `app/serve.py` (`playlist`)
- Modify: `app/api.py` (new model and route)
- Test: `tests/test_guideforge.py`

**Interfaces:**
- Produces: `m3u.with_login(text: str, username: str, password: str) -> str`
- Produces: `db.set_token_login(token: str, username: str | None, password: str | None) -> None`
- Produces: `db.token_login(token: str) -> tuple[str, str] | None` (only when both are set)
- Produces: `db.tokens()` rows gain `xtream_user` and `xtream_pass` (`None` when unset)
- Produces: `PUT /api/tokens/{token}/login`, body `{"xtream_user": str, "xtream_pass": str}`, returns `db.tokens()`. Task 2's editor calls it.

- [ ] **Step 1: Create the branch**

Run: `git switch -c per-viewer-login`

- [ ] **Step 2: Write the failing tests**

Add to `tests/test_guideforge.py`, and call `test_viewer_login()` after `test_serving()` in `__main__`:

```python
def test_viewer_login():
    old = ('#EXTM3U url-tvg="http://gf/u/k/epg.xml.gz"\n#EXTINF:-1 tvg-logo="http://logo/a/b/1.png",A\n'
           "http://prov:8080/user/old/103\nhttp://prov:8080/live/user/old/101.ts\nhttp://other/stream.m3u8\n")
    assert m3u.with_login(old, "new", "p@ss/1 %") == old.replace("user/old/", "new/p%40ss%2F1%20%25/")

    # an existing database gains the columns, and its viewers keep working without a login
    # (test_serving revoked the default key, so "Old viewer" is the only one)
    db.add_token("Old viewer")
    with db.connect() as con:
        con.execute("ALTER TABLE tokens DROP COLUMN xtream_user")
        con.execute("ALTER TABLE tokens DROP COLUMN xtream_pass")
    db.init()
    assert [(t["label"], t["xtream_user"], t["xtream_pass"]) for t in db.tokens()] == [("Old viewer", None, None)]

    http = TestClient(app)  # no `with`: test_serving already ran startup, and the scheduler is shut down
    auth = ("admin", "pw")
    for who in ("Mum", "Dad"):
        http.post("/api/tokens", auth=auth, json={"label": who})
    mum, dad = (next(t["token"] for t in db.tokens() if t["label"] == who) for who in ("Mum", "Dad"))
    streams = lambda key: [l for l in http.get(f"/u/{key}/playlist.m3u").text.splitlines() if not l.startswith("#")]

    before = http.get(f"/u/{mum}/playlist.m3u")
    r = http.put(f"/api/tokens/{mum}/login", auth=auth, json={"xtream_user": " mum ", "xtream_pass": " pa/ss 2 "})
    assert r.status_code == 200
    assert [(t["xtream_user"], t["xtream_pass"]) for t in r.json() if t["token"] == mum] == [("mum", "pa/ss 2")]

    # a player holding the old copy gets the new login, not a 304
    r = http.get(f"/u/{mum}/playlist.m3u", headers={"If-None-Match": before.headers["etag"]})
    assert r.status_code == 200
    mine = streams(mum)
    assert mine and all(s.startswith(url("live/mum/pa%2Fss%202/")) for s in mine)
    assert all(s.startswith(url("live/user/pa%20ss/")) for s in streams(dad))  # no login: the operator's

    assert http.put(f"/api/tokens/{mum}/login", auth=auth, json={"xtream_user": "mum", "xtream_pass": ""}).status_code == 400
    assert http.put(f"/api/tokens/{mum}/login", auth=auth, json={"xtream_user": "", "xtream_pass": ""}).status_code == 200
    assert streams(mum) == streams(dad)  # cleared: back to the operator's login
```

- [ ] **Step 3: Run the tests to make sure they fail**

Run: `.venv/bin/python tests/test_guideforge.py`
Expected: FAIL with `AttributeError: module 'app.m3u' has no attribute 'with_login'`

- [ ] **Step 4: Implement `m3u.with_login(text: str, username: str, password: str) -> str` in `app/m3u.py`**

Rewrite every line that is a whole `http(s)://host` stream address whose path `_XTREAM` recognises. Keep the scheme, the host, the `/live` prefix if there is one, and the stream number with its extension. Put in `quote(username, safe="")` and `quote(password, safe="")`. `#` lines are never touched. You may add capture groups to `_XTREAM` to do this, as long as `stream_key` still returns the stream number (the existing `test_playlist` pins it). Use a replacement function, not a replacement string, so backslashes in a password stay literal.

- [ ] **Step 5: Implement the storage in `app/db.py`**

- In `SCHEMA`, `tokens` gets `xtream_user TEXT, xtream_pass TEXT` (nullable; `NULL` means use the operator's login).
- In `init`, after `executescript(SCHEMA)`, add both columns with `ALTER TABLE tokens ADD COLUMN` when `PRAGMA table_info(tokens)` does not list `xtream_user`.
- `tokens()` also selects `xtream_user, xtream_pass`.
- `set_token_login(token, username, password)` updates both columns. `token_login(token)` returns `(user, pass)` only when both are non-empty, else `None`.

- [ ] **Step 6: Implement the route in `app/api.py`**

Model `ViewerLogin(BaseModel)` with `xtream_user: str = Field("", max_length=200)` and `xtream_pass: str = Field("", max_length=200)`. `PUT /tokens/{token}/login` strips both. If exactly one is empty, raise `HTTPException(400, "A viewer's login needs both a username and a password, or neither")`. Store blanks as `None`. Then, if `db.PLAYLIST.exists()`, call `db.PLAYLIST.touch()`. A new mtime gives the playlist a new ETag, so players holding the old login fetch it again (comment that in the code). Return `db.tokens()`.

- [ ] **Step 7: Implement the rewrite in `serve.playlist` (`app/serve.py`)**

After the `304` check, read the playlist body as text. When `key` has a `db.token_login(key)`, pass the body through `m3u.with_login(body, *login)`. Everything else about the response (guide line, gzip, headers) stays as it is.

- [ ] **Step 8: Run the tests to make sure they pass**

Run: `.venv/bin/python tests/test_guideforge.py`
Expected: last line `ok`

- [ ] **Step 9: Commit**

```bash
git add app/m3u.py app/db.py app/serve.py app/api.py tests/test_guideforge.py docs/superpowers
git commit -m "Give each viewer an optional provider login of their own"
```

---

### Task 2: Login fields on the Viewers page, and the docs

**Files:**
- Modify: `app/static/index.html` (`renderViewers`, the note under the Add viewer form)
- Modify: `README.md` (the `[!IMPORTANT]` box, the Viewer Addresses table)

**Interfaces:**
- Consumes: `PUT /api/tokens/{token}/login` and the `xtream_user` / `xtream_pass` fields on `s.tokens` from Task 1.

- [ ] **Step 1: Add the login form to each viewer in `renderViewers`**

Under the viewer's name and above Revoke, in the `.who` column, add a small form with:
- two `.field` text inputs, prefilled from `t.xtream_user` and `t.xtream_pass`, labelled "Provider username" and "Provider password", with `autocomplete="off"` and `spellcheck="false"` like the Source fields
- a `.btn` labelled "Save login"
- the note "Their own provider login. Leave both blank to use yours."

On submit, call `api("PUT", "/tokens/" + encodeURIComponent(t.token) + "/login", {xtream_user, xtream_pass}).then(refresh, fail)`. `viewersKey` already includes `s.tokens`, so a saved login re-renders the list.

- [ ] **Step 2: Rewrite the copy**

In `index.html`, replace the first sentence of the note after the Add viewer form ("The playlist hands a viewer your provider's stream addresses, login included, so give it only to people you would give that login to.") with:

> A viewer's playlist carries a provider login in its stream addresses: their own if you set one above, otherwise yours. Give a playlist without its own login only to people you would give your login to.

In `README.md`, replace the body of the `[!IMPORTANT]` box with:

> **Each viewer can have their own provider login.** The playlist contains your provider's stream addresses, login included. Set a viewer's own username and password under **Viewers** and their playlist carries that login instead of yours. A viewer without one gets yours, so give those addresses only to people you would give your login to. Each login's connection limit applies to the players using it.

In the Viewer Addresses table, the `/u/<key>/playlist.m3u` row becomes: "The edited playlist, with the viewer's own provider login when one is set. Its first line carries the viewer's guide address."

- [ ] **Step 3: Check it in the running app**

Run: `ADMIN_PASSWORD=dev DATA_DIR=$(mktemp -d) .venv/bin/uvicorn app.main:app --port 8765`, then open `http://localhost:8765`. Under Viewers, set a login on `default`, press Save login, reload the page, and check the fields come back filled. Clear both, save, and check they come back empty. Enter only a username, save, and check the error is shown. `.venv/bin/python tests/test_guideforge.py` still prints `ok`.

- [ ] **Step 4: Commit**

```bash
git add app/static/index.html README.md
git commit -m "Edit a viewer's provider login from the Viewers page"
```
