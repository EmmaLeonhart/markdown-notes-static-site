"""Writing the static site: one page per note, an index, and a stylesheet."""

from __future__ import annotations

import html
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from . import markdown
from .notes import Library, Note, discover

STYLE_CSS = """\
:root {
  --bg: #fdfcf9; --fg: #22211f; --muted: #6b675f; --link: #2457a6;
  --missing: #a63d24; --rule: #e4e0d6; --code-bg: #f2efe8;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #1b1a18; --fg: #e9e6df; --muted: #a39e93; --link: #8db4f0;
    --missing: #f0a08c; --rule: #3a3833; --code-bg: #2a2925;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--fg);
  font: 17px/1.6 Georgia, "Iowan Old Style", serif;
}
.page { max-width: 42rem; margin: 0 auto; padding: 1.5rem 1rem 3rem; }
nav.top { font-family: system-ui, sans-serif; font-size: 0.9rem; margin-bottom: 1.5rem; }
a { color: var(--link); }
a.missing, span.missing { color: var(--missing); text-decoration: underline dotted; }
h1, h2, h3, h4 { line-height: 1.25; }
code { background: var(--code-bg); padding: 0.1em 0.3em; border-radius: 3px; font-size: 0.9em; }
pre { background: var(--code-bg); padding: 0.8rem; overflow-x: auto; border-radius: 4px; }
pre code { background: none; padding: 0; }
blockquote { margin: 1rem 0; padding-left: 1rem; border-left: 3px solid var(--rule); color: var(--muted); }
img { max-width: 100%; }
hr { border: none; border-top: 1px solid var(--rule); }
.backlinks { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--rule); font-size: 0.95rem; }
.backlinks h2 { font-size: 1rem; font-family: system-ui, sans-serif; color: var(--muted); }
.backlinks p { color: var(--muted); }
.index-list .path { color: var(--muted); font-size: 0.85rem; margin-left: 0.4rem; }
"""

PAGE_TEMPLATE = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="page">
{nav}
<main>
{body}
</main>
{footer}
</div>
</body>
</html>
"""


@dataclass
class BuildResult:
    pages: int
    output: Path
    missing_links: List[str] = field(default_factory=list)  # "note.md -> target"
    duplicates: List[str] = field(default_factory=list)


def _e(text: str) -> str:
    return html.escape(text, quote=True)


def render_note(note: Note, library: Library, site_title: str, missing: Optional[List[str]] = None) -> str:
    """The full HTML page for one note."""

    def wikilink(target: str, label: Optional[str]) -> str:
        dest = library.resolve(target)
        text = _e(label or target)
        if dest is None:
            if missing is not None:
                missing.append(f"{note.path} -> {target}")
            return f'<span class="missing" title="No note named {_e(target)}">{text}</span>'
        return f'<a href="{_e(dest.filename)}">{text}</a>'

    body = markdown.render(note.text, wikilink)
    if note.title == note.name and not body.startswith("<h1>"):
        body = f"<h1>{_e(note.title)}</h1>\n{body}" if body else f"<h1>{_e(note.title)}</h1>"

    sources = library.backlinks_for(note)
    if sources:
        items = "\n".join(f'<li><a href="{_e(s.filename)}">{_e(s.title)}</a></li>' for s in sources)
        footer = (
            '<section class="backlinks">\n<h2>Pages that link here</h2>\n'
            f"<ul>\n{items}\n</ul>\n</section>"
        )
    else:
        footer = '<section class="backlinks">\n<h2>Pages that link here</h2>\n<p>None yet.</p>\n</section>'

    nav = f'<nav class="top"><a href="index.html">{_e(site_title)}</a></nav>'
    return PAGE_TEMPLATE.format(
        title=_e(f"{note.title} | {site_title}"), nav=nav, body=body, footer=footer
    )


def render_index(library: Library, site_title: str) -> str:
    """The index page: every note, alphabetically by title."""
    notes = sorted(library.notes, key=lambda n: (n.title.casefold(), n.path))
    if notes:
        items = []
        for n in notes:
            # Show the path when it adds something (a subfolder or a title
            # that differs from the file name).
            show_path = "/" in n.path or n.title != n.name
            path = f'<span class="path">{_e(n.path)}</span>' if show_path else ""
            items.append(f'<li><a href="{_e(n.filename)}">{_e(n.title)}</a>{path}</li>')
        listing = '<ul class="index-list">\n' + "\n".join(items) + "\n</ul>"
    else:
        listing = "<p>No notes found.</p>"
    count = f"<p>{len(notes)} note{'s' if len(notes) != 1 else ''}.</p>"
    body = f"<h1>{_e(site_title)}</h1>\n{count}\n{listing}"
    return PAGE_TEMPLATE.format(title=_e(site_title), nav="", body=body, footer="")


def build(source: Path, output: Path, site_title: Optional[str] = None) -> BuildResult:
    """Build the site for the notes in `source` into `output`.

    Existing files in `output` are overwritten; nothing is deleted.
    """
    source, output = Path(source), Path(output)
    if not source.is_dir():
        raise NotADirectoryError(f"notes folder not found: {source}")
    title = site_title or source.resolve().name or "Notes"
    notes = discover(source, exclude=[output])
    library = Library(notes)

    output.mkdir(parents=True, exist_ok=True)
    missing: List[str] = []
    for note in notes:
        page = render_note(note, library, title, missing)
        (output / note.filename).write_text(page, encoding="utf-8")
    (output / "index.html").write_text(render_index(library, title), encoding="utf-8")
    (output / "style.css").write_text(STYLE_CSS, encoding="utf-8")
    return BuildResult(pages=len(notes), output=output, missing_links=missing, duplicates=library.duplicates)
