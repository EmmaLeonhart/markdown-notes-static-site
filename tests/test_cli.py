import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from notes_to_site.cli import main

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "example"


class CliTests(unittest.TestCase):
    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_example_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "site"
            code, stdout, stderr = self.run_main(str(EXAMPLE), "-o", str(out), "--title", "Garden")
            self.assertEqual(code, 0, stderr)
            notes = sorted(p.stem for p in EXAMPLE.rglob("*.md"))
            self.assertIn(f"Wrote {len(notes)} pages", stdout)
            pages = {p.name for p in out.glob("*.html")}
            self.assertIn("index.html", pages)
            self.assertEqual(len(pages), len(notes) + 1)
            index = (out / "index.html").read_text(encoding="utf-8")
            self.assertIn("<h1>Garden</h1>", index)
            # Every internal href points at a page that exists.
            import re

            for page in out.glob("*.html"):
                for href in re.findall(r'href="([^"]+)"', page.read_text(encoding="utf-8")):
                    if "://" not in href:
                        self.assertTrue((out / href).exists(), f"{page.name} -> {href}")
            # The example has one deliberately missing link, reported as a warning.
            self.assertIn("warning: no note for link", stderr)

    def test_missing_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, stderr = self.run_main(str(Path(tmp) / "nope"))
            self.assertEqual(code, 2)
            self.assertIn("notes folder not found", stderr)

    def test_quiet(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, stdout, stderr = self.run_main(str(EXAMPLE), "-o", str(Path(tmp) / "s"), "-q")
            self.assertEqual((code, stdout, stderr), (0, "", ""))

    def test_python_dash_m(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, PYTHONPATH=str(ROOT))
            proc = subprocess.run(
                [sys.executable, "-m", "notes_to_site", str(EXAMPLE), "-o", str(Path(tmp) / "s"), "-q"],
                env=env, capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue((Path(tmp) / "s" / "index.html").exists())


if __name__ == "__main__":
    unittest.main()
