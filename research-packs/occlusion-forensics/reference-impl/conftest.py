"""Make the package importable regardless of pytest's invocation directory.

The pack ships as source inside a research repo rather than as an installed
distribution, so there is no site-packages entry to rely on. Without this,
`pytest` works from `reference-impl/` and fails from the repo root, which is
exactly where CI would run it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))
