import tempfile
import unittest
from pathlib import Path

from notes_to_site.notes import Library, discover, find_links, find_title, notes_from_texts, slugify


class HelperTests(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(slugify("My Note: Draft #2"), "my-note-draft-2")
        self.assertEqual(slugify("Café au lait"), "café-au-lait")
        self.assertEqual(slugify("???"), "note")

    def test_find_links_ignores_code(self):
        text = "See [[A]] and [[B|bee]].\n\n```\n[[NotALink]]\n```\nAlso `[[Nope]]` and [[ C ]]."
        self.assertEqual(find_links(text), ["A", "B", "C"])

    def test_find_title(self):
        self.assertEqual(find_title("\n# The Title\n\nbody", "file"), "The Title")
        self.assertEqual(find_title("body\n# Later heading", "file"), "file")
        self.assertEqual(find_title("", "file"), "file")


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.notes = notes_from_texts({
            "Alpha.md": "# Alpha\nLinks to [[beta]] twice: [[Beta|again]], and [[Missing]].",
            "Beta.md": "Back to [[Alpha]] and itself [[Beta]].",
            "sub/Gamma.md": "# Gamma note\nPoints at [[Alpha#Intro]] and [[sub/gamma]].",
        })
        self.lib = Library(self.notes)
        self.by_name = {n.name: n for n in self.notes}

    def test_resolve_case_insensitive(self):
        self.assertIs(self.lib.resolve("ALPHA"), self.by_name["Alpha"])

    def test_resolve_path_and_anchor(self):
        self.assertIs(self.lib.resolve("sub/Gamma"), self.by_name["Gamma"])
        self.assertIs(self.lib.resolve("Alpha#Intro"), self.by_name["Alpha"])
        self.assertIs(self.lib.resolve("Beta.md"), self.by_name["Beta"])

    def test_resolve_missing(self):
        self.assertIsNone(self.lib.resolve("Missing"))
        self.assertIsNone(self.lib.resolve("#only-anchor"))

    def test_backlinks(self):
        alpha, beta, gamma = (self.by_name[k] for k in ("Alpha", "Beta", "Gamma"))
        # Sorted by title; each source listed once; self-links excluded.
        self.assertEqual(self.lib.backlinks_for(alpha), [beta, gamma])
        self.assertEqual(self.lib.backlinks_for(beta), [alpha])
        self.assertEqual(self.lib.backlinks_for(gamma), [])

    def test_titles(self):
        self.assertEqual(self.by_name["Alpha"].title, "Alpha")
        self.assertEqual(self.by_name["Beta"].title, "Beta")
        self.assertEqual(self.by_name["Gamma"].title, "Gamma note")

    def test_duplicate_names(self):
        notes = notes_from_texts({"a/Same.md": "one", "b/Same.md": "two", "X.md": "[[same]]"})
        lib = Library(notes)
        self.assertEqual(lib.duplicates, ["b/Same.md"])
        self.assertEqual(lib.resolve("same").path, "a/Same.md")
        self.assertEqual(lib.resolve("b/same").path, "b/Same.md")
        self.assertEqual(sorted(n.slug for n in notes), ["same", "same-2", "x"])

    def test_reserved_slugs(self):
        notes = notes_from_texts({"Index.md": "", "style.md": ""})
        self.assertEqual(sorted(n.slug for n in notes), ["index-2", "style-2"])


class DiscoverTests(unittest.TestCase):
    def test_discover_skips_hidden_and_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sub").mkdir()
            (root / ".obsidian").mkdir()
            (root / "site").mkdir()
            (root / "One.md").write_text("# One\n[[Two]]", encoding="utf-8")
            (root / "sub" / "Two.md").write_text("two", encoding="utf-8")
            (root / ".obsidian" / "Hidden.md").write_text("x", encoding="utf-8")
            (root / "site" / "Old.md").write_text("x", encoding="utf-8")
            (root / "notes.txt").write_text("x", encoding="utf-8")
            notes = discover(root, exclude=[root / "site"])
            self.assertEqual([n.path for n in notes], ["One.md", "sub/Two.md"])
            self.assertEqual(notes[0].links, ["Two"])

    def test_discover_reads_utf8_with_bom(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Bom.md").write_bytes("﻿# Héllo".encode("utf-8"))
            (note,) = discover(root)
            self.assertEqual(note.title, "Héllo")


if __name__ == "__main__":
    unittest.main()
