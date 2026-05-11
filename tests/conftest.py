"""
Session-wide pytest configuration.

Sets QT_QPA_PLATFORM=offscreen before any Qt import so the test suite
runs in headless environments (CI, containers without libEGL/X11).
Must be the first file imported by pytest — conftest.py at the root of
the test directory is loaded before any test module.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
