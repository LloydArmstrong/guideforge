# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Static HTML, hand-written CSS and vanilla JS in one file (`app/static/index.html`), served by FastAPI. SortableJS is vendored. No Node toolchain and no build step. Chosen by the owner over React/Svelte + Tailwind.

## Users

One operator who self-hosts the app and maintains a TV guide for a handful of remote viewers (family, friends) watching through IPTV players such as TiviMate. The operator works at a desk on a big screen with keyboard and mouse. After the first setup, the job they come back for most is tidying the line-up: new channels appeared, the order drifted, something needs hiding or renaming.

The remote viewers never see this interface. They only paste a guide URL into their player.

## Product Purpose

Pull one upstream XMLTV guide on a schedule, apply the operator's line-up (order, visibility, names, channel numbers, logos), and serve the result as a compressed guide to many remote players. Success is a guide that stays correct in every player without the operator touching it, and a line-up that takes minutes, not an evening, to put right when upstream changes.

## Positioning

The line-up is saved once and re-applied to every future upstream sync. Channels the operator has never seen are appended to the end rather than silently reshuffling the guide, and each viewer gets their own revocable URL.

## Operating Context

- Upstream guides are large (50 MB and up, thousands of channels) and often slightly malformed.
- The guide is delivered over the open internet through a reverse proxy, a Cloudflare Tunnel, or an optional Cloudflare R2 mirror. Google Drive is explicitly not a distribution method.
- Players match programmes to channels by XMLTV channel id, so ids are never rewritten.
- Edits are published automatically a few seconds after the last change; there is no save or publish step.

## Capabilities and Constraints

- Channel editor: reordering by drag, by arrow keys, or by typing a position; per-channel enable, display name, channel number (LCN) and logo URL overrides, group assignment.
- Groups: XMLTV has no groups, so one is guessed per new channel and stays editable. A whole group can be enabled or disabled at once (a group with mixed settings asks first); new channels arriving in a fully disabled group stay hidden. "Gather groups" moves every channel next to the rest of its group in one step. There is deliberately no control that enables or disables every channel in the guide.
- Distribution: per-viewer keys, each with a guide URL per reachable base (local, public, R2 mirror) and a copy action aimed at TiviMate. Optional keyless public access.
- Sync: scheduled by interval or cron, manual "Sync now", last and next sync time, published file size, channel and programme counts, last error.
- The editor is protected by a single admin password (HTTP Basic). It may be reached over plain HTTP on a LAN, where the clipboard API is unavailable.
- Undecided: per-viewer line-ups (today every viewer receives the same guide).

## Brand Commitments

The name is GuideForge. No logo, palette or voice has been set by the owner.

## Evidence on Hand

No customers, testimonials or benchmarks exist and none may be invented. Real content comes from the operator's own upstream guide at runtime; channel names and logos shown in mock-ups or screenshots are synthetic.

## Product Principles

1. The line-up is the product: the channel list gets the space, everything else supports it.
2. Never surprise a running guide: no silent reordering, no half-written file, a failed sync keeps the last good guide.
3. State is always legible: the operator can tell at a glance whether what players download matches what the editor shows.
4. Thousands of rows are normal, not an edge case.

## Accessibility & Inclusion

Reordering must be possible from the keyboard, not only by dragging. Every control carries a text label, and focus is always visible.
