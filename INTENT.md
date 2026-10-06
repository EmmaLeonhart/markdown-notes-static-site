# What this project is for

_Maintained by Claude: a running read of what the user is trying to do. It is
analysis, not a transcript, and it changes as understanding improves._

## Current understanding

Build the tool described in `data_lake/brief.md`: a small command-line tool,
Python standard library only, that takes a folder of Markdown notes and writes
a static HTML site:

- one HTML page per note;
- an index page listing the notes;
- `[[note name]]` wiki-links between notes, rendered as links;
- a "pages that link here" (backlinks) section at the bottom of each page;
- tests and a README.

## What supports it

- `data_lake/brief.md` (the only material, dropped by the user) states the task.
- The folder name the user chose, `notes-to-site`, matches the brief.
- Chat: the user has said nothing yet. The intake ran at 2026-10-05 19:11 PST
  with verdict WORK MODE (material present, no engagement).

## Assumptions (made without asking; the user can overturn any of them)

- The Markdown converter is written by hand (stdlib has none) and covers the
  common subset: headings, paragraphs, emphasis, inline code, fenced code
  blocks, lists, block quotes, ordinary links, horizontal rules. Not full
  CommonMark.
- Notes are `*.md` files found recursively; a note's name is its file name
  without `.md`. `[[Name]]` matches names case-insensitively. `[[Name|label]]`
  shows `label`. A link to a missing note renders as plain text marked as
  missing, not as a broken link.
- Output file names are slugs of the note names; the index lists notes
  alphabetically by title.
- Packaged as a pip-installable module with a console script, Python 3.9+,
  tests with stdlib `unittest`, CI on GitHub Actions.

## Constraints from the user

- Standard library only (from the brief).
- Repository stays private unless the user says otherwise (cleanvibe rule).

## Open questions

- Should note titles come from the first `# heading` or the file name? (Assumed:
  file name for linking, first heading shown as the page title if present.)
- Any styling wishes for the generated site? (Assumed: one small built-in
  stylesheet.)

## Confidence

High on the goal (the brief is explicit). Medium on the details listed under
Assumptions.

## Timeline

- Work mode started: 2026-10-05 19:11 PST (intake verdict).
