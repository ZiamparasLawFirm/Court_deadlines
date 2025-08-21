
# -*- coding: utf-8 -*-
"""
deadlines.pdf
Provides GREEK_FONT_PATH for app.py to ensure Greek-capable font is available.
"""
import os

_PKG_DIR = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(_PKG_DIR, "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

GREEK_FONT_PATH = os.path.join(ASSETS_DIR, "DejaVuSans.ttf")
