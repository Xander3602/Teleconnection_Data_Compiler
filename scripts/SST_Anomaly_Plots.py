import os
import pandas as pd
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

from paths import DATA_DIR, output_dir_for

main_development_region_atlantic = {"North": 20, "South": 8, "West": -65, "East": -10}
mediterranean_sea = {"North": 45, "South": 30, "West": 0, "East": 35}
western_indian_ocean = {"North": 10, "South": -10, "West": 50, "East": 70}
eastern_indian_ocean = {"North": 10, "South": -10, "West": 90, "East": 110}
Gulf_of_Mexico = {"North": 30, "South": 20, "West": -100, "East": -80}
Gulf_of_Alaska = {"North": 60, "South": 45, "West": -165, "East": -125}
Gulf_of_Guinea = {"North": 10, "South": -5, "West": -15, "East": 10}



def partition_sst_by_region(sst: xr.Dataset, region: dict) -> xr.Dataset:
    """
    Partition the SST data by the given region.
    Args:
        sst: xarray.Dataset containing SST data
        region: dictionary containing the North, South, West, and East boundaries of the region
    Returns:
        xarray.Dataset containing the SST data for the given region
    """
    lon_360 = sst.lon.where(sst.lon >= 0, sst.lon + 360)
    west = region["West"] + 360 if region["West"] < 0 else region["West"]
    east = region["East"] + 360 if region["East"] < 0 else region["East"]

    partition = sst.where((sst.lat > region["South"]) & (sst.lat < region["North"]))
    partition = partition.where((lon_360 >= west) & (lon_360 <= east))
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