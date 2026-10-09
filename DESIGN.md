---
name: GuideForge
description: A self-hosted TV guide editor set like the printed listings page it produces.
colors:
  ink: "#1C1B1A"
  ink-hover: "#3B3936"
  red: "#C4221A"
  moving: "color-mix(in srgb, #C4221A 22%, #EFEDE6)"
  paper: "#EFEDE6"
  paper-lit: "#F7F5EF"
  white: "#FFFFFF"
  ink-soft: "#57544E"
  blank: "#85827A"
  rule: "#C3BFB5"
typography:
  display:
    fontFamily: "Archivo, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "2.75rem"
    fontWeight: 800
    lineHeight: 1.05
    letterSpacing: "0.01em"
    fontVariation: "'wdth' 62"
  headline:
    fontFamily: "Archivo, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 800
    lineHeight: 1.05
    letterSpacing: "0.01em"
    fontVariation: "'wdth' 62"
  section:
    fontFamily: "Archivo, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 800
    lineHeight: 1.05
    letterSpacing: "0.01em"
    fontVariation: "'wdth' 62"
  title:
    fontFamily: "Archivo, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 800
    lineHeight: 1.05
    letterSpacing: "0.01em"
    fontVariation: "'wdth' 62"
  figure:
    fontFamily: "Archivo, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 800
    lineHeight: 1.45
    fontVariation: "'wdth' 62"
  name:
    fontFamily: "Archivo, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "1rem"
    fontWeight: 700
    lineHeight: 1.45
    fontVariation: "'wdth' 75"
  control:
    fontFamily: "Archivo, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 700
    lineHeight: 1.45
    fontVariation: "'wdth' 75"
  label:
    fontFamily: "Archivo, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 700
    lineHeight: 1.45
    fontVariation: "'wdth' 75"
  body:
    fontFamily: "Archivo, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.45
    fontFeature: "'tnum'"
  small:
    fontFamily: "Archivo, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.45
  mono:
    fontFamily: "ui-monospace, 'SF Mono', Menlo, monospace"
    fontSize: "0.8125rem"
    fontWeight: 400
rounded:
  none: "0"
spacing:
  cell: "8px"
  gutter-narrow: "16px"
  section-gap: "18px"
  gutter: "28px"
  column-gap: "32px"
  row: "36px"
components:
  button:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.control}"
    rounded: "{rounded.none}"
    padding: "6px 14px"
  button-hover:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    typography: "{typography.control}"
    rounded: "{rounded.none}"
    padding: "6px 14px"
  button-primary-hover:
    backgroundColor: "{colors.ink-hover}"
    textColor: "{colors.paper}"
  button-danger:
    backgroundColor: "transparent"
    textColor: "{colors.red}"
    typography: "{typography.control}"
    rounded: "{rounded.none}"
    padding: "6px 14px"
  button-danger-hover:
    backgroundColor: "{colors.red}"
    textColor: "{colors.white}"
  button-disabled:
    backgroundColor: "transparent"
    textColor: "{colors.ink-soft}"
  field:
    backgroundColor: "{colors.paper-lit}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "7px 8px"
  field-address:
    backgroundColor: "{colors.paper-lit}"
    textColor: "{colors.ink}"
    typography: "{typography.mono}"
    rounded: "{rounded.none}"
    padding: "7px 8px"
  nav-link:
    textColor: "{colors.ink}"
    typography: "{typography.name}"
    padding: "2px 0"
  column-head:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    padding: "6px 8px 5px"
  row:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    height: "{spacing.row}"
  row-hover:
    backgroundColor: "{colors.paper-lit}"
  row-moving:
    backgroundColor: "{colors.moving}"
  row-off:
    textColor: "{colors.ink-soft}"
  cell:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "0 8px"
  cell-focus:
    backgroundColor: "{colors.white}"
  number-box:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    typography: "{typography.figure}"
    rounded: "{rounded.none}"
    padding: "0 2px"
    width: "54px"
  number-box-hover:
    backgroundColor: "{colors.paper-lit}"
    textColor: "{colors.ink}"
  number-box-off:
    backgroundColor: "transparent"
    textColor: "{colors.ink-soft}"
  section-head:
    textColor: "{colors.ink}"
    typography: "{typography.section}"
    padding: "7px 0 5px"
---

# Design System: GuideForge

## Overview

**Creative North Star: "The Listings Page"**

GuideForge's editor is set like the printed weekly TV listings spread it produces. A masthead in compressed heavy capitals sits over a thick-and-thin rule; one edition line under it says whether what players download matches the page; the line-up below is the page itself, each channel led by a reversed ink number box, with a bold section head printed wherever the group changes. It is a working sheet for one operator at a desk on a big screen in daylight, and it is light only: there is no dark theme.

The material is newsprint and ink. A grey paper ground, soft-black ink, hairline rules, and a single spot red. Everything is flat and square. Structure is carried by rule weight and by one typeface's width axis, never by boxes, cards, tints or depth. Density is high because thousands of rows are normal: a row is 36px tall and the list gets the width. The system refuses the home-lab dashboard: no sidebar of icons, no status cards, no dark slate.

Almost nothing moves. Rows slide out of the way while one is dragged, and the edition line flashes once in fresh ink when a new edition is published.

**Key Characteristics:**
- Newsprint ground, soft-black ink, hairline rules, one spot red.
- One grotesque, Archivo, with its width axis doing the hierarchy.
- Flat ink, square corners, no shadows as depth, no texture.
- Fields are ruled blanks on the sheet, not boxes.
- Section heads re-set on every reorder and show exactly where a group is split.
- Dense, ruled, tabular; the line-up is the page.
- Light only. Two authored movements and nothing else.

## Colors

Two inks on grey paper: soft black does all the work and one red marks what is in motion, wrong, or current.

### Primary
- **Ink** (#1C1B1A): all reading text, every heavy rule, the reversed number boxes, and solid primary actions (Sync now, Save, Add viewer). 14.7:1 on the paper.
- **Ink, pressed lighter** (#3B3936): the hover state of a solid ink button, and nothing else.

### Secondary
- **Stop-Press Red** (#C4221A): the one spot colour. It appears as text on the edition line while changes are unpublished ("Stop press") or a sync has failed, on the alert line and its rule, on the last error in the sync record, as the small square before the current view name and the current group filter, as the outline and text of the destructive Revoke action, on "not in upstream", and as the text caret. About 5:1 on the paper, so it is legible as body text. It is deliberately darker than the #D5281F on the direction card, which reached only about 4.3:1.
- **Moving** (red mixed 22% into the paper): the fill of the row being dragged. The only diluted use of red.

### Neutral
- **Newsprint** (#EFEDE6): the page ground, and the text colour reversed out of ink. The owner's chosen value.
- **Lit Paper** (#F7F5EF): a field at rest, or a row under the pointer or holding focus.
- **White** (#FFFFFF): the one cell being typed in within a lit row, and the text on a hovered Revoke button. Nowhere else.
- **Soft Ink** (#57544E): secondary text: notes, counts, channel IDs, logo addresses, group names in rows, disabled channels, placeholders, the grip. 6.4:1 on the paper.
- **Blank Line** (#85827A): the line under a field, dashed disabled outlines, the outline of a disabled channel's number box. 3.3:1, for lines only, never for text.
- **Hairline** (#C3BFB5): rules between rows, between cells, and between list items.

Channel logos are the operator's upstream content and bring their own colour. A disabled channel's logo is greyscaled at 55% opacity.

### Named Rules
**The Stop Press Rule.** Red means in motion, wrong, or current, and nothing else. If an element is none of those three, it is ink. Red is never decoration, never a brand flourish, and there is no second accent.

**The Solid Ink Rule.** Primary actions are solid ink with paper text. A primary action is never red; the only red button is the destructive one, and it is an outline until hovered.

## Typography

**Display Font:** Archivo variable, at 62% width and weight 800 (with Helvetica Neue, Arial, sans-serif)
**Body Font:** Archivo variable, at normal width and weight 400 (same fallback)
**Label/Mono Font:** ui-monospace, SF Mono, Menlo, on copy-exact tokens only

**Character:** One self-hosted grotesque set three ways. Compressed and heavy it shouts like a listings masthead; narrowed and bold it labels; at normal width it reads. Figures are tabular everywhere so counts and times align in columns.

### Hierarchy
- **Display** (800, 62% width, 2.75rem, 1.05, uppercase, 0.01em): the GuideForge wordmark in the masthead. 2rem at 1000px and below.
- **Headline** (800, 62% width, 1.5rem, 1.05, uppercase): the title of a view (Viewers, Source).
- **Section** (800, 62% width, 1.375rem, 1.05, uppercase): the section head printed above the first row of each run of a group.
- **Title** (800, 62% width, 1.125rem, 1.05, uppercase): minor heads: Groups, a viewer's name, Sync record, empty-state heads.
- **Figure** (800, 62% width, 1.0625rem): the position number in a number box.
- **Name** (700, 75% width, 1rem): the channel display name in a row, and, in uppercase, the three view names on the edition line.
- **Control** (700, 75% width, 0.875rem): button labels, in sentence case.
- **Label** (700, 75% width, 0.75rem, uppercase): the column headings over the line-up.
- **Body** (400, normal width, 0.875rem, 1.45, tabular figures): everything read at length. Notes are capped at 68ch, empty states at 60ch.
- **Small** (400, 0.8125rem): channel IDs and help text under form fields.
- **Mono** (ui-monospace, 0.8125rem): viewer guide addresses and inline code.

Two heavier body weights exist for emphasis within running text: 650 for form labels, the All channels line, and red stop-press text; 800 for the selected group name.

### Named Rules
**The One Grotesque Rule.** Everything is Archivo. Hierarchy comes from the width axis and weight, not from a second family: 62% and 800 for heads and figures, 75% and 700 for names, controls and labels, normal width for reading.

**The Copy-Exact Exception.** Monospace appears only on strings the operator copies character for character: viewer guide addresses and inline code. It is never a style choice.

## Layout

One page, three views (Line-up, Viewers, Source) switched by the address hash; the masthead and edition line stay put above all of them. The page is capped at 1680px with 28px side gutters, and nothing is centred inside it: everything hangs from the left edge of the sheet.

The Line-up view is two columns: a 250px sticky index of groups and the listings column taking the rest, 32px apart. Each listing row is a nine-track grid (grip 22px, number box 54px, enable tick 30px, logo 40px, display name, LCN 70px, channel ID, logo address, group 120px) with a minimum height of 36px, so the list keeps a 37px rhythm including its hairline. The column headings stick to the top of the window while the list scrolls. Off-screen rows skip rendering, which keeps thousands of channels quick. Viewers are a 240px name column beside their address lines; Source is a form up to 560px wide beside the sync record.

Spacing is set by hand per relationship rather than from a numeric scale. The fixed measures are the 8px cell padding, the 36px row, the 18px gap above a section head, and the 28px gutter.

There is one breakpoint, at 1000px. Below it the gutters drop to 16px, every two-column layout becomes one column, the group index stops being sticky and sits above the list, and the line-up keeps its columns at fixed widths inside a horizontally scrolling sheet (866px minimum) rather than collapsing a row into a card.

### Named Rules
**The Running Head Rule.** A section head is printed wherever the group changes between two consecutive visible rows, with that run's channel count at its right. A group split in two therefore reads as two sections, which is how the operator finds drift. When the groups are scattered (more runs than three times the number of groups) no heads are printed at all, the count line says so, and Gather groups is offered.

## Elevation & Depth

There is none. The sheet is one flat plane of paper; nothing floats, overlaps, or casts a shadow, and there are no modals, popovers or raised cards. State is shown by a change of paper tone (lit paper under the hand, white in the cell being typed in, the red-tinted moving row) and by rule weight. Sticky column headings stay legible by being opaque paper, not by a shadow.

### Named Rules
**The Flat Ink Rule.** No shadow is ever used as depth. The shadow property appears only as an inset line: 1px of Blank Line under a hovered cell, 2px of the text colour under an overridden cell. Likewise the gradient function is used only to lay a flat fill or a ruled blank sheet, never a visible blend. No texture, grain, or paper effect.

## Shapes

Every corner is square (0 radius), on buttons, fields, number boxes and markers alike. Form is made of rules in a fixed weight order: 4px ink under the masthead, 3px ink above every section head and block head, 1px ink for the edition line and the top of an index, 1px Hairline between rows, cells and list items, 1px Blank Line under a field. Outlines are 1px. The only filled shapes are the number boxes, solid ink buttons, and the small red square marker (about half an em) for the current view and group. The only pictogram is the six-dot grip.

### Named Rules
**The Ruled Blank Rule.** A field is a blank on the sheet: lit paper with a single line beneath it and no outline. In a listing row the blank loses even that, and is just a cell between hairlines until hovered. Never draw a box around an input.

**The Rule Weight Rule.** Heavier rule, bigger division: 4px for the page, 3px for a section, 1px ink for a band, 1px hairline for a row. A new division picks one of these; it does not invent a weight.

## Components

### Buttons
Blunt printed labels: narrow bold type in a square 1px ink outline.
- **Shape:** square (0 radius), 6px 14px padding, Control type, never wraps.
- **Primary:** solid ink with paper text. Hover lightens the ink slightly.
- **Default:** transparent with an ink outline. Hover reverses to solid ink with paper text.
- **Destructive:** red outline and red text. Hover fills red with white text. Used for Revoke only, and always behind a confirmation.
- **Disabled:** dashed Blank Line outline, Soft Ink text, no fill.
- **Press / Focus:** the button sits 1px lower while pressed, instantly, with no transition. Focus is a 2px ink outline offset 2px, as on every control.

### Inputs / Fields
- **Style:** Lit Paper fill, no outline, a 1px Blank Line beneath, 7px 8px padding. The line turns ink on hover. Placeholders are Soft Ink at full opacity. The caret is red.
- **Address field:** the same blank, read-only, set in Mono, selecting its whole contents on focus, with a "Copy for TiviMate" button beside it.
- **Form field:** a 650-weight label above, Small help text below, 16px between fields.
- **Checkbox:** the native control at 15px, tinted ink.
- **Focus:** the 2px ink outline; inside a listing row it is drawn inset and the cell turns white.

### Navigation
The three view names sit at the left of the edition line in Name type, uppercase, 20px apart, with no underline until hovered. The current view is marked by a small red square before its name, not by weight or colour of the text.

### Masthead and Edition Line
The wordmark in Display type at the left and the day's date in Body at the right, over a 4px ink rule. Three pixels below, the edition line runs between two 1px ink rules: view names, then one status sentence (publish time, channel and programme counts, file size, next sync), then Sync now at the right end. The sentence turns red and begins "Stop press" while changes are unpublished or a sync is running, and carries the error when a sync fails. When a new edition lands, the sentence flashes once from reversed ink back to paper over 0.9s. An alert, when present, is one red line under it with a red rule and a Dismiss button.

### Group Index
A list of every group under a 3px ink rule: whole-group checkbox, group name, enabled over total in Soft Ink. Lines are separated by hairlines. The first line, All channels, has an ink rule, 650 weight and no checkbox. Selecting a name filters the list; the selected name goes to 800 weight with the red square before it.

### Listing Row
The signature component. Grip, number box, enable tick, logo, then cells divided by vertical hairlines: display name in Name type, LCN, channel ID, logo address, group. Secondary cells are Soft Ink.
- **Number box:** reversed, paper figures on solid ink in Figure type. It is a field: typing a number moves the channel there. Hover or focus flips it to ink on lit paper.
- **Hover / focus within:** the row turns Lit Paper.
- **Overridden cell:** a 2px underline in the text colour marks a value that departs from upstream; clearing the cell removes it.
- **Disabled channel:** the whole row drops to Soft Ink, the number box becomes an outline, the logo greys.
- **Gone upstream:** "not in upstream" follows the channel ID in red.
- **Dragging:** the row being moved takes the Moving fill while its neighbours slide aside over 150ms on an ease-out curve (cubic-bezier(.16, 1, .3, 1)). Arrow keys, Home and End on the grip do the same without a pointer.
- **Section head:** Section type over a 3px ink rule with 18px above, the run's channel count at the right in Soft Ink. The first visible head has no rule or gap.

### Record and Empty States
The sync record is a definition list under a Title head and 3px rule: a 110px Soft Ink term, the value beside it, hairlines between. Before the first load the list area is a ruled blank sheet of hairlines at the row rhythm. An empty view is a Title head and one plain paragraph that says what to do next.

### Named Rules
**The Two Movements Rule.** Only two things animate: rows displacing during a drag (150ms ease-out) and the fresh-ink flash on the edition line when a new edition is published (0.9s, once). Reduced motion turns both off. Hover, focus, view changes and state changes are instant.

## Do's and Don'ts

### Do:
- **Do** set every head in Archivo at 62% width, weight 800, uppercase, and pick its size from the four that exist: 2.75rem, 1.5rem, 1.375rem, 1.125rem.
- **Do** keep red for things in motion, wrong, or current, at #C4221A so red text holds about 5:1 on the paper.
- **Do** make primary actions solid ink with paper text.
- **Do** build fields as ruled blanks: lit paper, one line beneath, no outline.
- **Do** divide with rules from the existing weights (4px, 3px and 1px ink, 1px hairline) and keep every corner square.
- **Do** keep figures tabular and keep secondary text at Soft Ink or darker.
- **Do** print a section head wherever the group changes, and print none when the groups are scattered.
- **Do** keep reordering possible from the keyboard and by typing a position, and keep the 2px ink focus outline on every control.
- **Do** keep the line-up a table at every width; let it scroll sideways below 1000px.

### Don't:
- **Don't** use red for a primary action, a heading, a link, or emphasis. Don't add a second accent colour.
- **Don't** add a dark theme. The system is light only by decision.
- **Don't** use a shadow for depth, round a corner, or add texture, grain or a visible gradient.
- **Don't** draw a box around an input or wrap content in a card.
- **Don't** bring in a second typeface. Monospace is for viewer guide addresses and inline code only.
- **Don't** build the home-lab dashboard: no sidebar of icons, no status cards, no dark slate.
- **Don't** animate anything beyond the drag displacement and the fresh-ink flash.
- **Don't** set text in Blank Line or Hairline; they are for lines.
- **Don't** use white as a surface. It is the cell being typed in and the text on a hovered Revoke, and nothing more.
