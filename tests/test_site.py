import tempfile
import unittest
from pathlib import Path

from notes_to_site.notes import Library, notes_from_texts
from notes_to_site.site import build, render_index, render_note


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.notes = notes_from_texts({
            "Alpha.md": "# Alpha\nSee [[Beta]], [[beta|the second]] and [[Nowhere]].",
            "Beta.md": "Just text <b>here</b>.",
            "sub/Gamma.md": "# Gamma & co\n[[Alpha]]",
        })
        self.lib = Library(self.notes)
        self.n = {note.name: note for note in self.notes}

    def test_note_page_links_and_missing(self):
        missing = []
        page = render_note(self.n["Alpha"], self.lib, "My Notes", missing)
        self.assertIn('<a href="beta.html">Beta</a>', page)
        self.assertIn('<a href="beta.html">the second</a>', page)
        self.assertIn('<span class="missing" title="No note named Nowhere">Nowhere</span>', page)
        self.assertEqual(missing, ["Alpha.md -> Nowhere"])
        self.assertIn("<title>Alpha | My Notes</title>", page)
        self.assertIn('<a href="index.html">My Notes</a>', page)
        # The note's own heading is not duplicated.
        self.assertEqual(page.count("<h1>"), 1)

    def test_backlinks_section(self):
        page = render_note(self.n["Alpha"], self.lib, "S")
        self.assertIn("Pages that link here", page)
        self.assertIn('<li><a href="gamma.html">Gamma &amp; co</a></li>', page)
        beta = render_note(self.n["Beta"], self.lib, "S")
        self.assertIn('<li><a href="alpha.html">Alpha</a></li>', beta)
        gamma = render_note(self.n["Gamma"], self.lib, "S")
        self.assertIn("<p>None yet.</p>", gamma)

    def test_note_without_heading_gets_one(self):
        page = render_note(self.n["Beta"], self.lib, "S")
        self.assertIn("<h1>Beta</h1>", page)
        self.assertIn("&lt;b&gt;here&lt;/b&gt;", page)

    def test_index_lists_notes_by_title(self):
        page = render_index(self.lib, "My Notes")
        a, b, g = (page.index(f'href="{s}.html"') for s in ("alpha", "beta", "gamma"))
        self.assertLess(a, b)
        self.assertLess(b, g)
        self.assertIn('<span class="path">sub/Gamma.md</span>', page)
        self.assertIn("<p>3 notes.</p>", page)


class BuildTests(unittest.TestCase):
    def test_build_writes_site(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "notes"
            src.mkdir()
            (src / "One.md").write_text("# One\n[[Two]] [[Ghost]]", encoding="utf-8")
            (src / "Two.md").write_text("two", encoding="utf-8")
            out = src / "site"  # output inside the notes folder
            result = build(src, out)
            self.assertEqual(result.pages, 2)
            self.assertEqual(result.missing_links, ["One.md -> Ghost"])
            self.assertEqual(sorted(p.name for p in out.iterdir()), ["index.html", "one.html", "style.css", "two.html"])
            self.assertIn("<title>notes</title>", (out / "index.html").read_text(encoding="utf-8"))
            # A second build does not pick up anything from the output folder.
            (out / "Stray.md").write_text("x", encoding="utf-8")
            self.assertEqual(build(src, out, "Title").pages, 2)

    def test_build_missing_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(NotADirectoryError):
                build(Path(tmp) / "nope", Path(tmp) / "out")


if __name__ == "__main__":
    unittest.main()
