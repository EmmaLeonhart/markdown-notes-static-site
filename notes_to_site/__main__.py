"""Allow `python -m notes_to_site`."""

import sys

from .cli import main

sys.exit(main())
