"""Command line: notes-to-site SOURCE [-o OUTPUT] [--title TITLE]."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .site import build


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="notes-to-site",
        description="Turn a folder of Markdown notes into a static HTML site "
        "with an index page and backlinks. Link notes with [[note name]].",
    )
    parser.add_argument("source", type=Path, help="folder of Markdown (.md) notes")
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("site"),
        help="folder to write the site into (default: ./site)",
    )
    parser.add_argument("--title", help="site title (default: the notes folder's name)")
    parser.add_argument("-q", "--quiet", action="store_true", help="print nothing but errors")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    try:
        result = build(args.source, args.output, args.title)
    except NotADirectoryError as exc:
        print(f"notes-to-site: {exc}", file=sys.stderr)
        return 2

    if not args.quiet:
        for path in result.duplicates:
            print(f"warning: {path} has the same name as another note; [[links]] by name go to the first one",
                  file=sys.stderr)
        for link in result.missing_links:
            print(f"warning: no note for link {link}", file=sys.stderr)
        plural = "" if result.pages == 1 else "s"
        print(f"Wrote {result.pages} page{plural} and an index to {result.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
