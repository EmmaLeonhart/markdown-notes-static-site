# Queue

Concrete, not-yet-done steps. Finished items are deleted from here and logged
in `devlog.md` in the same commit.

4. Site builder (`notes_to_site/site.py`): one page per note, index page,
   backlinks section, missing-link marking, built-in stylesheet. Unit tests.
5. CLI (`notes_to_site/cli.py`): `notes-to-site SOURCE [-o OUT]`, also
   `python -m notes_to_site`. End-to-end test on a sample notes folder.
6. CI: `.github/workflows/ci.yml` running the tests on Linux/Windows/macOS.
7. README: install, usage, link syntax, what Markdown is supported.
