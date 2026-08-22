"""conftest.py for held-out tests.

Makes _helpers importable from any test subdirectory.
"""
import sys
import os

_HELPERS = os.path.join(os.path.dirname(__file__), "_helpers")
if _HELPERS not in sys.path:
    sys.path.insert(0, _HELPERS)
