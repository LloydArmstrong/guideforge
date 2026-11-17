# Per-viewer provider login

## Why

The operator manages IPTV subscriptions for friends and family. Everyone should get the one line-up and guide the operator arranges, but each person's playlist must carry their own provider login, so each subscription's connection limit applies to its own holder.

## Goals

- A viewer can have its own provider username and password.
- That viewer's playlist carries their login in every stream address.
- A viewer with no login gets the operator's login, exactly as today.
- Changing a viewer's login takes effect on their next playlist refresh, with no sync.

## Non-goals

- Different providers per viewer. All subscriptions are with the same provider, so stream numbers, line-up and guide are shared.
- A separate list of subscriptions. Two devices on one subscription are two viewers with the same login.
- Checking a login against the provider on save, and showing subscription expiry. Easy follow-ups if wanted.

## Approaches

1. **Swap the login at serve time (chosen).** The published playlist is built once, as now. When a viewer with a login fetches it, the username and password segments of each Xtream-shaped stream address are replaced with theirs. One file, instant effect.
2. Build one playlist file per viewer at sync time. More files, and a login change waits for the next sync.
3. Generate stream addresses from the database per request. More code and slower for no gain.

## Design

- `tokens` gains nullable `xtream_user` and `xtream_pass` columns (migrated in place for existing databases).
- The Viewers page shows username and password fields per viewer, editable and saved through the management API.
- `serve.playlist` rewrites `.../USER/PASS/<stream id>` addresses (with or without `/live`) to the viewer's login when one is set, URL-quoted as `xtream.py` does. Works whether Source uses the Xtream login or an Xtream-shaped M3U link.
- Line-up, guide, sync and the server address are unchanged. The sync still reads channels with the operator's login.
- The README's "Everyone shares your provider login" warning is rewritten.
- One test: a viewer with a login gets it in the addresses; a viewer without gets the operator's.

## Left to the builder

- Exact rewrite expression, API shape and field layout on the Viewers page, following existing patterns.
