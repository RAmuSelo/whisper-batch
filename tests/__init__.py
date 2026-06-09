"""Test package bootstrap.

Ensures the ``src/`` layout is importable so the suite runs from a fresh
checkout with plain ``python3 -m unittest discover -s tests`` (no editable
install, no network, no whisper required).
"""

import os
import sys

_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "src"))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
