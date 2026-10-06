# notes-to-site

A small command-line tool that turns a folder of Markdown notes into a static
HTML site:

- one page per note,
- an index page listing every note,
- links between notes written as `[[note name]]`,
- a **Pages that link here** (backlinks) section at the bottom of each page.

Python standard library only: no dependencies. Python 3.9 or newer.

## Install

```
pip install .
```

(or run it without installing: `python -m notes_to_site ...` from this folder).

## Use

```
notes-to-site path/to/notes -o site --title "My Notes"
```

| Option | Meaning |
| --- | --- |
| `SOURCE` | Folder of `.md` notes, searched recursively. |
| `-o`, `--output` | Where to write the site. Default: `./site`. |
| `--title` | Site title. Default: the notes folder's name. |
| `-q`, `--quiet` | Print nothing but errors. |

Open `site/index.html` in a browser. The output is plain HTML and one
stylesheet (`style.css`, light and dark), so it can be hosted anywhere static
files are served.

Try it on the bundled example: `notes-to-site example -o site`.

## Linking notes

| You write | You get |
| --- | --- |
| `[[Composting]]` | a link to `Composting.md`, shown as "Composting" |
| `[[Composting\|the compost note]]` | the same link, shown as "the compost note" |
| `[[plants/Tomatoes]]` | a link by path, for when two notes share a name |
| `[[Composting#Turning]]` | a link to the page (the `#section` part is ignored for now) |

- A note's name is its file name without `.md`. Matching ignores case.
- If two notes in different folders share a name, `[[name]]` goes to the first
  by path, and the tool prints a warning; link by path to reach the other.
- A link to a note that doesn't exist is shown in a muted style and listed as a
  warning when building.
- `[[...]]` inside code (`` `like this` `` or a fenced block) is left alone.
- Backlinks list each linking page once, sorted by title. A note's links to
  itself are not counted.

## Pages and titles

- A note whose first line is a `# Heading` uses it as its title; otherwise the
  file name is the title and is shown as the page's heading.
- Page file names are lowercase slugs of the note names (`My Note.md` →
  `my-note.html`), made unique if two clash. `index` and `style` are reserved.
- Folders and files starting with `.` (such as `.obsidian/`), and folders
  starting with `_`, are skipped. If the output folder is inside the notes
  folder, it is skipped too.
- Building writes over existing files in the output folder but never deletes
  anything. After renaming or removing notes, clear the folder yourself.

## Markdown supported

A practical subset, not full CommonMark: `#` headings, paragraphs, `*em*` /
`_em_`, `**strong**`, `~~strikethrough~~`, `` `code` ``, fenced code blocks
(with a language class), ordered and unordered lists (nested, tight or
loose), `>` block quotes, `[links](url "title")`, `![images](src)`,
`<https://autolinks>`, horizontal rules, and hard line breaks (two trailing
spaces). Raw HTML in notes is escaped and shown as text. Tables, footnotes
and front matter are not handled.

Images and other non-Markdown files are not copied into the site; an image
path is used as written.

## Develop

```
python -m unittest discover -s tests
```

CI runs the tests on Linux, Windows and macOS with Python 3.9 and 3.13.

## Project notes

Started with [cleanvibe](https://github.com/EmmaLeonhart/cleanvibe) on
2026-10-05 from the brief in `data_lake/brief.md`. `INTENT.md` holds the
working assumptions, `queue.md` / `todo.md` / `devlog.md` the plan and the
history, and `sessions/` the Claude session transcripts. Run `cleanvibe` in
this folder (or double-click `!runClaude.bat` on Windows) to open a new
session here.
