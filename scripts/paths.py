"""
Centralized path definitions for Teleconnection Data Compiler.
All scripts should import from here instead of repeating os.path logic.
"""
import os

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
ENSO_DATA_DIR = os.path.join(DATA_DIR, "enso")
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")

# Default watermark logo path (used by ENSO, daily index, IOD scripts)
WATERMARK_FILENAME = "aura-logo-square-trans (2).png"
WATERMARK_LOGO_PATH = os.path.join(ASSETS_DIR, WATERMARK_FILENAME)


def output_dir_for(topic: str) -> str:
    """Return output directory path for a given topic (e.g. 'enso', 'daily_index', 'epo')."""
    return os.path.join(PROJECT_ROOT, "output", topic)
