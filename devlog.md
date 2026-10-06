# Devlog

Where "done" lives: dated entries, newest last.

## 2026-10-05

- 19:11 PST: thirty-minute intake ran; verdict WORK MODE (brief in
  `data_lake/`, no chat). Wrote `INTENT.md`, created the private GitHub repo
  `EmmaLeonhart/markdown-notes-static-site` and pushed. Update check: the
  vendored skills already match cleanvibe v2.0.4. Planned the build into
  `queue.md`.
- Package skeleton: `pyproject.toml` (setuptools, no dependencies, Python
  3.9+, `notes-to-site` console script) and the `notes_to_site` package.
- Markdown converter (`notes_to_site/markdown.py`): headings, paragraphs,
  emphasis, strikethrough, inline and fenced code, nested ordered/unordered
  lists (tight and loose), block quotes, links, images, autolinks, rules,
  hard breaks; wiki-links go to a callback. 29 unit tests pass.
- Notes and links (`notes_to_site/notes.py`): recursive `*.md` discovery
  (hidden and `_` folders and the output folder skipped), titles from a
  first-line `# heading`, unique slugs (`index`/`style` reserved), wiki-links
  outside code, case-insensitive resolution by name or by path, `#section`
  ignored, backlinks without self-links or repeats. 41 tests pass.
