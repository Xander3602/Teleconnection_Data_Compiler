import os
import argparse
import pandas as pd
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

from paths import NOAA_SST_MEAN_DIR, output_dir_for

# =============================================================================
# CONFIGURATION — edit this block or override via command line (see --help)
# =============================================================================

CONFIG = {
    # Years to overlay (must have sst.day.mean.YEAR.nc in NOAA_SST_MEAN_DIR)
    "years_to_plot": [2026, 2023, 2018, 2014, 2009, 2006, 2002, 1997],
    # Which year to highlight as "current" (solid black line)
    "current_year": 2026,
    # Region(s) to plot: one or more keys from REGIONS below
    "regions": ["Gulf_of_Guinea"],
    # Long-term mean (climatology) overlay: filename in NOAA_SST_MEAN_DIR, or None to skip
    "ltm_filename": "sst.day.mean.ltm.1991-2020.nc",
    "ltm_label": "LTM 1991-2020",
    "ltm_linestyle": "--",
    "ltm_linewidth": 2.0,
    "ltm_color": "gray",
    # Figure size (width, height) in inches
    "figsize": (12, 5),
    # Output: DPI and whether to show the plot window after saving
    "dpi": 300,
    "show_plot": True,
    # Line style for the current year vs other years
    "current_year_linestyle": "-",
    "current_year_linewidth": 2.5,
    "other_years_linestyle": "--",
    "other_years_alpha": 0.8,
}

# Predefined region boxes: North, South, West, East (degrees). Add your own here.
REGIONS = {
    "main_development_region_atlantic": {"North": 20, "South": 8, "West": -65, "East": -10},
    "mediterranean_sea": {"North": 45, "South": 30, "West": 0, "East": 35},
    "western_indian_ocean": {"North": 10, "South": -10, "West": 50, "East": 70},
    "eastern_indian_ocean": {"North": 10, "South": -10, "West": 90, "East": 110},
    "Gulf_of_Mexico": {"North": 30, "South": 20, "West": -100, "East": -80},
    "Gulf_of_Alaska": {"North": 60, "South": 45, "West": -165, "East": -125},
    "Gulf_of_Guinea": {"North": 10, "South": -5, "West": -15, "East": 10},
}



def partition_sst_by_region(sst: xr.Dataset, region: dict) -> xr.Dataset:
    """
    Partition the SST data by the given region.
    Handles regions that cross the 0° longitude line (e.g. Gulf of Guinea).
    """
    lon_360 = sst.lon.where(sst.lon >= 0, sst.lon + 360)
    west = region["West"] + 360 if region["West"] < 0 else region["West"]
    east = region["East"] + 360 if region["East"] < 0 else region["East"]

    partition = sst.where((sst.lat > region["South"]) & (sst.lat < region["North"]))
    # Region crosses 0° when west > east in 0–360 (e.g. West=-15, East=10 → west=345, east=10)
    if west > east:
        partition = partition.where((lon_360 >= west) | (lon_360 <= east))
    else:
        partition = partition.where((lon_360 >= west) & (lon_360 <= east))
    return partition

def calculate_daily_average_sst_anomaly(sst: xr.Dataset, region: dict) -> tuple:
    """
    Calculate the daily average SST for the given region.
    Returns:
        day_of_year: array of day-of-year (1-365/366) for overlay comparison
        daily_averages: list of daily average SST values
    """
    partition = partition_sst_by_region(sst, region)
    daily_averages = []
    times = []
    for time in partition.time:
        daily_average = partition.sel(time=time).mean(dim=["lat", "lon"])
        times.append(time.values)
        daily_averages.append(float(daily_average.values))
    # Convert to day-of-year so all years overlay on same x-axis
    times_arr = np.array(times)
    if times_arr.dtype.kind == "M" or str(times_arr.dtype).startswith("datetime"):
        doy = pd.to_datetime(times_arr).dayofyear.values
    else:
        # cftime or other: use pandas if possible
        doy = pd.DatetimeIndex(pd.to_datetime([str(t) for t in times_arr])).dayofyear.values
    return doy, np.array(daily_averages)


def parse_args():
    """Parse CLI overrides; values from CONFIG are used when not specified."""
    p = argparse.ArgumentParser(
        description="Plot SST daily mean by year (overlaid by day of year).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--years",
        type=int,
        nargs="+",
        default=None,
        metavar="YEAR",
        help="Years to plot (e.g. 2026 2025 2023). Overrides CONFIG['years_to_plot'].",
    )
    p.add_argument(
        "--current-year",
        type=int,
        default=None,
        metavar="YEAR",
        help="Year to highlight as current. Overrides CONFIG['current_year'].",
    )
    p.add_argument(
        "--region",
        type=str,
        nargs="+",
        default=None,
        metavar="REGION",
        help="One or more region keys. Overrides CONFIG['regions']. e.g. --region mediterranean_sea Gulf_of_Mexico",
    )
    p.add_argument(
        "--no-show",
        action="store_true",
        help="Save figure but do not show plot window.",
    )
    p.add_argument(
        "--list-regions",
        action="store_true",
        help="Print available region keys and exit.",
    )
    return p.parse_args()


def main():
    args = parse_args()
    if args.list_regions:
        print("Available regions:", ", ".join(REGIONS.keys()))
        return

    # Merge CONFIG with CLI overrides
    years_to_plot = args.years if args.years is not None else CONFIG["years_to_plot"]
    current_year = args.current_year if args.current_year is not None else CONFIG["current_year"]
    show_plot = not args.no_show and CONFIG["show_plot"]

    # Normalize regions to a list (support CONFIG["regions"] or legacy CONFIG["region"])
    if args.region is not None:
        regions_to_plot = list(args.region)
    else:
        raw = CONFIG.get("regions", CONFIG.get("region", "mediterranean_sea"))
        regions_to_plot = [raw] if isinstance(raw, str) else list(raw)

    unknown = [r for r in regions_to_plot if r not in REGIONS]
    if unknown:
        print(f"Unknown region(s): {unknown}. Use --list-regions to see options.")
        return

    output_dir = output_dir_for("sst")
    os.makedirs(output_dir, exist_ok=True)
    cmap = plt.cm.viridis
    other_years = [y for y in years_to_plot if y != current_year]

    for region_idx, region_key in enumerate(regions_to_plot):
        region_config = REGIONS[region_key]
        fig, ax = plt.subplots(figsize=CONFIG["figsize"])

        # Plot long-term mean first (so it sits behind the year curves) if configured
        ltm_filename = CONFIG.get("ltm_filename")
        if ltm_filename:
            ltm_path = os.path.join(NOAA_SST_MEAN_DIR, ltm_filename)
            if os.path.isfile(ltm_path):
                with xr.open_dataset(ltm_path, use_cftime=True) as ds_ltm:
                    sst_ltm = ds_ltm.sst.where(ds_ltm.sst.notnull())
                    doy_ltm, values_ltm = calculate_daily_average_sst_anomaly(sst_ltm, region_config)
                ax.plot(
                    doy_ltm,
                    values_ltm,
                    color=CONFIG.get("ltm_color", "gray"),
                    linestyle=CONFIG.get("ltm_linestyle", "--"),
                    linewidth=CONFIG.get("ltm_linewidth", 2.0),
                    label=CONFIG.get("ltm_label", "LTM"),
                    zorder=0,
                )
            else:
                print(f"LTM file not found, skipping: {ltm_path}")

        for i, year in enumerate(years_to_plot):
            nc_path = os.path.join(NOAA_SST_MEAN_DIR, f"sst.day.mean.{year}.nc")
            if not os.path.isfile(nc_path):
                print(f"Skip {year}: file not found {nc_path}")
                continue
            ds = xr.open_dataset(nc_path)
            sst = ds.sst.where(ds.sst.notnull())
            day_of_year, daily_averages = calculate_daily_average_sst_anomaly(sst, region_config)
            ds.close()
            is_current = year == current_year
            if is_current:
                ax.plot(
                    day_of_year,
                    daily_averages,
                    color="black",
                    linestyle=CONFIG["current_year_linestyle"],
                    linewidth=CONFIG["current_year_linewidth"],
                    label=f"{year} (current)",
                    zorder=2,
                )
            else:
                j = other_years.index(year)
                color = cmap(j / max(len(other_years) - 1, 1))
                ax.plot(
                    day_of_year,
                    daily_averages,
                    color=color,
                    linestyle=CONFIG["other_years_linestyle"],
                    alpha=CONFIG["other_years_alpha"],
                    label=str(year),
                    zorder=1,
                )

        # X-axis: day-of-year (1-366) with month labels
        ax.set_xlim(1, 366)
        month_starts = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
        month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        ax.set_xticks(month_starts)
        ax.set_xticklabels(month_labels)
        ax.set_xlabel("Day of year")
        ax.set_ylabel("SST daily mean (°C)")
        region_label = region_key.replace("_", " ").title()
        ax.set_title(f"SST daily average — {region_label} — by year (overlaid by day of year)")
        ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        out_name = f"sst_{region_key}_daily_avg.png"
        out_path = os.path.join(output_dir, out_name)
        plt.savefig(out_path, dpi=CONFIG["dpi"], bbox_inches="tight")
        print(f"Saved: {out_path}")
        if show_plot:
            plt.show()
        else:
            plt.close()


if __name__ == "__main__":
    main()