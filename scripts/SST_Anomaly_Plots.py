import os
import pandas as pd
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

from paths import DATA_DIR, output_dir_for

main_development_region = {"North": 20, "South": 8, "West": 295, "East": 350}
mediterranean_sea = {"North": 45, "South": 30, "West": 0, "East": 35}


def partition_sst_by_region(sst: xr.Dataset, region: dict) -> xr.Dataset:
    """
    Partition the SST data by the given region.
    Args:
        sst: xarray.Dataset containing SST data
        region: dictionary containing the North, South, West, and East boundaries of the region
    Returns:
        xarray.Dataset containing the SST data for the given region
    """
    partition = sst.where((sst.lat > region["South"]) & (sst.lat < region["North"]))
    partition = partition.where((partition.lon >= region["West"]) & (partition.lon <= region["East"]))
    return partition

def calculate_daily_average_sst_anomaly(sst: xr.Dataset, region: dict) -> xr.Dataset:
    """
    Calculate the daily average SST anomaly for the given region.
    Args:
        sst: xarray.Dataset containing SST data
        region: dictionary containing the North, South, West, and East boundaries of the region
    Returns:
        dates: list of dates
        daily_average: list of daily average SST anomalies
    """
    partition = partition_sst_by_region(sst, region)
    daily_averages = []
    dates = []
    for time in partition.time:
        daily_average = partition.sel(time=time).mean(dim=["lat", "lon"])
        dates.append(time.values)
        daily_averages.append(daily_average.values)
    return dates, daily_averages


def main():
    output_dir = output_dir_for("sst")
    os.makedirs(output_dir, exist_ok=True)
    ds = xr.open_dataset(os.path.join(DATA_DIR, "sst.day.mean.2026.nc"))
    sst = ds.sst.where(ds.sst.notnull())
    dates, daily_averages = calculate_daily_average_sst_anomaly(sst, mediterranean_sea)
    plt.plot(dates, daily_averages)
    plt.savefig(os.path.join(output_dir, "sst_mediterranean_daily_avg.png"), dpi=300, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    main()