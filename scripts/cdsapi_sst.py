"""
Download ECMWF seasonal SST anomaly NetCDF for Niño 3.4 region via CDS API.
Requires: pip install cdsapi and ~/.cdsapirc with API key.
Output: data/enso/ssta_YYYY_MM.nc (used by enso_sst_plot.py).
"""
import os
import cdsapi

from paths import ENSO_DATA_DIR

os.makedirs(ENSO_DATA_DIR, exist_ok=True)

# Edit year/month as needed
YEAR = "2026"
MONTH = "03"
OUTPUT_FILE = os.path.join(ENSO_DATA_DIR, f"ssta_{YEAR}_{MONTH}.nc")

dataset = "seasonal-postprocessed-single-levels"
request = {
    "originating_centre": "ecmwf",
    "system": "51",
    "variable": ["sea_surface_temperature_anomaly"],
    "product_type": ["monthly_mean"],
    "year": [YEAR],
    "month": [MONTH],
    "leadtime_month": ["1", "2", "3", "4", "5", "6"],
    "data_format": "netcdf",
    "area": [5, -170, -5, -120],  # Niño 3.4 region
}


def main():
    c = cdsapi.Client()
    c.retrieve(dataset, request, OUTPUT_FILE)
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
