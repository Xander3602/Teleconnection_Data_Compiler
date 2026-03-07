# Teleconnection Visuals

Scripts and data for plotting climate teleconnection indices (ENSO, AAO, EPO, IOD, sea ice, SST anomalies).

## Directory structure

```
Teleconnection_Data_Compiler/   # project root
├── data/              # Input CSVs and NetCDF files
│   ├── enso/          # ENSO seasonal NetCDFs (e.g. ssta_YYYY_MM.nc from CDS)
│   ├── enso.csv       # ENSO region indices (used by plotting_enso.py, enso_sst_plot.py)
│   ├── aao.csv
│   ├── soi.csv
│   ├── epo.reanalysis.1948-present.csv
│   ├── JMA_IOD_Data*.csv
│   └── *.nc           # Other NetCDFs (SST, sea ice) in data/
├── scripts/           # Python plotting and data-fetch scripts
│   ├── paths.py       # Centralized paths (DATA_DIR, output_dir_for, etc.)
│   ├── plotting_enso.py    # ENSO region time-series plots
│   ├── enso_sst_plot.py   # ENSO ensemble SST anomaly (forecast + analog years)
│   ├── cdsapi_sst.py      # Download ENSO SST anomaly NetCDF from CDS
│   ├── plotting_daily_index.py
│   ├── EPO_Data.py
│   ├── IOD_Plotting.py    # IOD area chart (was IDO_Plotting)
│   ├── IOD_formatting.py # JMA IOD wide → long CSV (was IOD_formating)
│   ├── SST_Anomaly_Plots.py
│   └── sea_ice.py
├── output/            # Generated plots
│   ├── enso/          # ENSO region plots + sst_anomaly.png
│   ├── daily_index/
│   ├── epo/
│   ├── iod/
│   ├── sst/
│   └── sea_ice/
├── assets/            # Logos/watermarks (e.g. aura-logo-square-trans (2).png)
├── requirements.txt   # Python dependencies
└── README.md
```

## Data files

Place in **`data/`** (or **`data/enso/`** for ENSO NetCDFs):

| File / folder | Used by |
|---------------|--------|
| `enso.csv` | `plotting_enso.py`, `enso_sst_plot.py` |
| `data/enso/ssta_YYYY_MM.nc` | `enso_sst_plot.py` (from `cdsapi_sst.py`) |
| `aao.csv` | `plotting_daily_index.py` |
| `soi.csv` | (SOI index if needed) |
| `epo.reanalysis.1948-present.csv` | `EPO_Data.py` |
| `JMA_IOD_Data.csv`, `JMA_IOD_Data_long.csv` | `IOD_formatting.py`, `IOD_Plotting.py` |
| `sst.day.mean.2026.nc` | `SST_Anomaly_Plots.py` |
| `sst.day.anom.2026.nc` | (optional; for anomaly plots) |
| `icec.day.mean.2026.nc`, `icec.day.mean.ltm.1991-2020.nc` | `sea_ice.py` |

All NetCDF files belong in **`data/`** or **`data/enso/`**; scripts load them from there.

## Assets

Place in **`assets/`**:

- `aura-logo-square-trans (2).png` — watermark used by ENSO, daily index, and IOD scripts (path: `assets/aura-logo-square-trans (2).png`, centralized in `scripts/paths.py`)

## Setup

### 1. Create a Python environment (recommended)

From the project root, create a virtual environment and install dependencies:

```bash
# One-time on Debian/Ubuntu if venv is not available:
#   sudo apt install python3.12-venv

./scripts/setup_venv.sh
source .venv/bin/activate   # Linux/macOS
# Or on Windows:  .venv\Scripts\activate
```

Then install dependencies (if you didn’t use the script):

```bash
pip install -r requirements.txt
```

### 2. Alternative: install without a venv

From the project root (use a venv in production to avoid conflicts):

```bash
pip install -r requirements.txt
```

CDS download also requires `~/.cdsapirc` with your API key (see [CDS API](https://cds.climate.copernicus.eu/api-how-to)).

## Running scripts

From the project root (with the virtual environment activated, or use `.venv/bin/python`):

```bash
# ENSO region plots (Niño 1+2, 3, 3.4, 4)
python scripts/plotting_enso.py

# ENSO ensemble SST anomaly (forecast + analog years); requires data/enso/ssta_YYYY_MM.nc
python scripts/enso_sst_plot.py

# Download ENSO SST anomaly NetCDF from CDS (requires ~/.cdsapirc)
python scripts/cdsapi_sst.py

# Daily index (e.g. AAO) — edit INPUT_CSV in script for other indices
python scripts/plotting_daily_index.py

# EPO index comparison
python scripts/EPO_Data.py

# IOD area chart (requires JMA IOD long-format data)
python scripts/IOD_Plotting.py

# Format JMA IOD wide → long CSV
python scripts/IOD_formatting.py

# SST anomaly (Mediterranean example)
python scripts/SST_Anomaly_Plots.py

# Sea ice concentration (Baltic/Black Sea)
python scripts/sea_ice.py
```

Generated plots go to **`output/`** in script-specific subfolders: `output/enso/`, `output/daily_index/`, `output/epo/`, `output/iod/`, `output/sst/`, `output/sea_ice/`.
