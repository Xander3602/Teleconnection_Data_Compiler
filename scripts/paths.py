"""
Centralized path definitions for Teleconnection Data Compiler.
All scripts should import from here instead of repeating os.path logic.
"""
import os

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)

# Data files live in Documents/data_fetcher (expanduser for portability)
DATA_DIR = os.path.expanduser(os.path.join("~", "Documents", "data_fetcher"))
ENSO_DATA_DIR = os.path.join(DATA_DIR, "enso")

# NOAA NetCDF data: three product types in subdirectories (names match data_fetcher)
NOAA_SST_MEAN_DIR = os.path.join(DATA_DIR, "NOAA_sst.day.mean")   # sst.day.mean.*.nc
NOAA_SST_ANOM_DIR = os.path.join(DATA_DIR, "NOAA_sst.day.anom")   # sst.day.anom.*.nc
NOAA_SEA_ICE_DIR = os.path.join(DATA_DIR, "NOAA_icec.day.mean")   # icec.day.mean.*.nc
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")

# Default watermark logo path (used by ENSO, daily index, IOD scripts)
WATERMARK_FILENAME = "aura-logo-square-trans (2).png"
WATERMARK_LOGO_PATH = os.path.join(ASSETS_DIR, WATERMARK_FILENAME)


def output_dir_for(topic: str) -> str:
    """Return output directory path for a given topic (e.g. 'enso', 'daily_index', 'epo')."""
    return os.path.join(PROJECT_ROOT, "output", topic)
