"""Shared test helpers.

Makes the ``src/`` layout importable without requiring an editable install, so
the suite runs from a fresh checkout with plain ``python3 -m unittest``.
"""

import os
import sys

_SRC = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, "src")
)
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)


def touch(path: str, content: str = "") -> None:
    """Create a file (and parent dirs) with optional content."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
