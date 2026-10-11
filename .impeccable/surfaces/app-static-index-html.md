---
version: 1
slug: "app-static-index-html"
primary_target: "app/static/index.html"
related_targets: []
---

# Editor (app/static/index.html)

Scope: the whole management UI, one static page with three views (Line-up, Viewers, Source). Visitor mode: Operate.

Audience and job: the operator at a desk on a big screen, keyboard and mouse, daylight. Comes back mainly to tidy the line-up after upstream changes: reorder, hide, rename. Handing out viewer URLs and checking sync health are secondary and must stay one click away.

Constraints: single HTML file, hand-written CSS, vanilla JS, vendored SortableJS and Archivo, no build step. Thousands of rows. May be served over plain HTTP on a LAN.

Chosen direction: The Listings Page. Memorable moment: the line-up re-typesets itself while a row is in the hand, a channel dragged across a section head visibly joining the group it lands in.

Unresolved: none.

## Direction contract

THESIS: The editor is set like the printed TV listings page it produces. It refuses the home-lab dashboard: no sidebar of icons, no status cards, no dark slate. The line-up is the page.

OWN-WORLD: Grey newsprint ground, soft-black ink, hairline rules, and a single spot red reserved for things in motion or wrong (unpublished changes, errors, the current view, destructive actions). One grotesque, Archivo, with its width axis doing the work: compressed heavy caps for the masthead, section heads and reversed number boxes; normal width for everything read at length. Square corners, flat ink, no shadows. Fields are ruled blanks on the sheet, not boxes. Primary actions are solid ink.

STORY: The operator sees at once whether what players download matches the page (the edition line), puts groups in the order players should show them (the Groups index), moves channels by dragging them into place or onto a group, by arrow keys, or by typing a position, and sees the edition line hold "unpublished changes" until a sync, by Sync now or on the daily schedule, prints the new edition.

FIRST VIEWPORT: At 1440 wide: a masthead with the GuideForge wordmark in compressed heavy caps at about 44px over a thick-and-thin rule; beneath it one edition line carrying publish time, channel and programme counts, file size and next sync, with Sync now at its right end and the three view names at its left. Below, two columns: a 250px Groups index in player order (every group with a grip, its enabled count and a whole-group checkbox, and a New group field beneath) and the listings column filling the rest, showing the group being read (or search results across groups, capped), each row led by a reversed ink number box under that group's bold section head.

FORM: Printed weekly TV listings spread; position 1 on the ordered list, taken by the owner over the rolled candidate 3. Seed key 2c31399b. Signature interaction: a channel dragged across a section head, or dropped on a group in the index, joins that group, with heads and counts re-setting as it moves; typing a number into a number box moves that channel there. Motion grammar: 150ms ease-out for row displacement while dragging; one authored moment, a fresh-ink flash on the edition line when a new edition is published; nothing else moves.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
