# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Static HTML, hand-written CSS and vanilla JS in one file (`app/static/index.html`), served by FastAPI. SortableJS is vendored. No Node toolchain and no build step. Chosen by the owner over React/Svelte + Tailwind.

## Users

One operator who self-hosts the app and maintains a channel line-up and TV guide for a handful of remote viewers (family, friends) watching through IPTV players such as TiviMate. The operator works at a desk on a big screen with keyboard and mouse. After the first setup, the job they come back for most is tidying the line-up: new channels appeared, the order drifted, something needs hiding or renaming.

The remote viewers never see this interface. They only paste a playlist address into their player.

## Product Purpose

Decide which channels and groups remote players show, and in what order. GuideForge pulls the provider's playlist and an XMLTV guide, applies the operator's line-up (groups, order, visibility, names, channel numbers, logos, guide matching), and serves an edited playlist and a matching compressed guide to many remote players. Success is a line-up that looks the way the operator arranged it in every player, stays correct without being touched, and takes minutes, not an evening, to put right when upstream changes.

## Positioning

The line-up is saved once and re-applied to every future upstream sync. Channels the operator has never seen join the end of their group rather than silently reshuffling anything, and each viewer gets their own revocable addresses.

## Operating Context

- Upstream guides are large (50 MB and up, thousands of channels) and often slightly malformed.
- The guide is delivered over the open internet through a reverse proxy, a Cloudflare Tunnel, or an optional Cloudflare R2 mirror. Google Drive is explicitly not a distribution method.
- Players take channels, their order and their groups from the playlist, never from the guide. That is why GuideForge serves the playlist.
- Players match programmes to channels by id. A guide channel's id is never rewritten; each stream instead names the guide channel it takes programmes from.
- Nothing is fetched or published as a side effect of editing. A sync runs only when the operator presses Sync now or on the schedule (daily by default); until then edits are saved and shown as unpublished.
- The published playlist carries the provider's stream addresses, login included, so every viewer shares the operator's one provider account and its connection limit.

## Capabilities and Constraints

- Sources: an M3U playlist address (for an Xtream Codes login, its get.php link) and an XMLTV guide address. Live channels only; film and series entries are left out. With no playlist, the guide's own channels are the line-up and only a guide is published.
- Channel editor: reordering by drag, by arrow keys, or by typing a position; per-channel enable, display name, channel number (LCN), logo address and guide id overrides. A stream whose guide id matches nothing in the guide is flagged.
- Groups are first-class and ordered: they start as the provider's own, and can be created, renamed (or merged by renaming onto an existing name), reordered and, once empty, removed. A channel changes group by being dragged across a section head, dropped on a group in the index, or by its Group field. A whole group can be enabled or disabled at once (a group with mixed settings asks first); new channels arriving in a fully disabled group stay hidden. There is deliberately no control that enables or disables every channel at once.
- Distribution: per-viewer keys, each with a playlist address and a guide address per reachable base (local, public; the R2 mirror carries the guide only) and a copy action aimed at TiviMate. The playlist names the viewer's guide address, so a player needs only the one. Optional keyless public access.
- Sync: scheduled by cron or interval, manual "Sync now", last and next sync time, guide size, channel, guide-match and programme counts, last error. If a download fails, edits that were waiting are still published from the last good download.
- The editor is protected by a single admin password (HTTP Basic). It may be reached over plain HTTP on a LAN, where the clipboard API is unavailable.
- Undecided: per-viewer line-ups (today every viewer receives the same playlist and guide); emulating the Xtream Codes API so players keep their film and series sections.

## Brand Commitments

The name is GuideForge. No logo, palette or voice has been set by the owner.

## Evidence on Hand

No customers, testimonials or benchmarks exist and none may be invented. Real content comes from the operator's own upstream guide at runtime; channel names and logos shown in mock-ups or screenshots are synthetic.

## Product Principles

1. The line-up is the product: the channel list gets the space, everything else supports it.
2. Never surprise a running line-up: no silent reordering, no half-written file, nothing published by accident, and a failed sync keeps the last good edition.
3. State is always legible: the operator can tell at a glance whether what players download matches what the editor shows.
4. Thousands of rows are normal, not an edge case.

## Accessibility & Inclusion

Reordering must be possible from the keyboard, not only by dragging. Every control carries a text label, and focus is always visible.
