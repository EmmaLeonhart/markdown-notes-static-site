"""Finding notes, resolving wiki-links between them, and computing backlinks."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .markdown import WIKILINK_RE

# Slugs reserved for files the site builder writes itself.
RESERVED_SLUGS = {"index", "style"}

_FENCED_RE = re.compile(r"^ {0,3}(`{3,}|~{3,}).*?(?:^ {0,3}\1[`~]*[ \t]*$|\Z)", re.M | re.S)
_CODE_SPAN_RE = re.compile(r"(`+).+?\1", re.S)
_H1_RE = re.compile(r"^ {0,3}#[ \t]+(.+?)[ \t]*#*[ \t]*$")


@dataclass
class Note:
    name: str  # file name without .md; what [[links]] refer to
    path: str  # path relative to the notes folder, with forward slashes
    text: str
    title: str = ""
    slug: str = ""
    links: List[str] = field(default_factory=list)  # raw link targets, in order

    @property
    def filename(self) -> str:
        return f"{self.slug}.html"


def slugify(name: str) -> str:
    """A file-name-safe slug: lowercase word characters joined by hyphens."""
    slug = re.sub(r"[^\w]+", "-", name.lower(), flags=re.UNICODE).strip("-_")
    return slug or "note"


def strip_code(text: str) -> str:
    """Remove fenced code blocks and code spans, where [[...]] is not a link."""
    text = _FENCED_RE.sub("", text)
    return _CODE_SPAN_RE.sub("", text)


def find_links(text: str) -> List[str]:
    """The wiki-link targets in `text`, in order, ignoring code."""
    return [m.group(1).strip() for m in WIKILINK_RE.finditer(strip_code(text))]


def find_title(text: str, fallback: str) -> str:
    """The note's first-line `# heading` if it has one, else `fallback`."""
    for line in text.splitlines():
        if not line.strip():
            continue
        m = _H1_RE.match(line)
        return m.group(1) if m else fallback
    return fallback


def _skip(rel: Path) -> bool:
    return any(part.startswith(".") or part.startswith("_") for part in rel.parts[:-1]) or rel.name.startswith(".")


def discover(source: Path, exclude: Iterable[Path] = ()) -> List[Note]:
    """Every `*.md` note under `source`, sorted by path.

    Hidden files and folders (starting with "." or, for folders, "_") are
    skipped, as is anything under a path in `exclude` (the output folder, if it
    sits inside the notes folder).
    """
    source = Path(source)
    excluded = [Path(p).resolve() for p in exclude]
    notes: List[Note] = []
    for path in sorted(source.rglob("*.md")):
        if not path.is_file():
            continue
        rel = path.relative_to(source)
        if _skip(rel):
            continue
        resolved = path.resolve()
        if any(resolved == ex or ex in resolved.parents for ex in excluded):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        notes.append(Note(name=path.stem, path=rel.as_posix(), text=text))
    _assign(notes)
    return notes


def _assign(notes: List[Note]) -> None:
    """Fill in titles, unique slugs and links."""
    used = set(RESERVED_SLUGS)
    for note in notes:
        note.title = find_title(note.text, note.name)
        base = slugify(note.name)
        slug, n = base, 2
        while slug in used:
            slug, n = f"{base}-{n}", n + 1
        used.add(slug)
        note.slug = slug
        note.links = find_links(note.text)


def notes_from_texts(texts: Dict[str, str]) -> List[Note]:
    """Build notes from {relative path: text}; for tests and library use."""
    notes = [
        Note(name=Path(rel).stem, path=Path(rel).as_posix(), text=text)
        for rel, text in sorted(texts.items())
    ]
    _assign(notes)
    return notes


class Library:
    """A set of notes with link resolution and backlinks."""

    def __init__(self, notes: List[Note]):
        self.notes = notes
        self._by_name: Dict[str, Note] = {}
        self._by_path: Dict[str, Note] = {}
        self.duplicates: List[str] = []  # names shared by more than one note
        for note in notes:
            key = note.name.casefold()
            if key in self._by_name:
                self.duplicates.append(note.path)
            else:
                self._by_name[key] = note
            self._by_path[note.path[: -len(".md")].casefold()] = note
        self.backlinks: Dict[str, List[Note]] = {note.path: [] for note in notes}
        for note in notes:
            seen = set()
            for target in note.links:
                dest = self.resolve(target)
                if dest is None or dest is note or dest.path in seen:
                    continue
                seen.add(dest.path)
                self.backlinks[dest.path].append(note)
        for sources in self.backlinks.values():
            sources.sort(key=lambda n: n.title.casefold())

    def resolve(self, target: str) -> Optional[Note]:
        """The note a `[[target]]` points to, or None.

        Matches the note name case-insensitively; a target with a "/" matches
        the note's path within the notes folder. A "#section" suffix is ignored.
        """
        target = target.split("#", 1)[0].strip()
        if target.lower().endswith(".md"):
            target = target[:-3]
        if not target:
            return None
        key = target.casefold()
        if "/" in key:
            return self._by_path.get(key.strip("/"))
        return self._by_name.get(key)

    def backlinks_for(self, note: Note) -> List[Note]:
        return self.backlinks[note.path]
