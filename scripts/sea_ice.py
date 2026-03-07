"""
Sea ice concentration map with climatology overlay and ice edge.
Switch REGION to plot Baltic, Black Sea, or other defined regions.
"""
import os
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from scipy.ndimage import gaussian_filter
from shapely.geometry import Point
from shapely.ops import unary_union

from paths import DATA_DIR, output_dir_for

OUTPUT_DIR = output_dir_for("sea_ice")

# Colormap: light blue = no ice (0), deep blue = full ice (1).
_WHITE_TO_BLUE = ["#ffffff", "#deebf7", "#9ecae1", "#4292c6", "#08519c", "#08306b"]
ICE_CMAP = mcolors.LinearSegmentedColormap.from_list("ice_coverage", _WHITE_TO_BLUE, N=256)
ICE_CMAP.set_bad(color="none")
REGION = "Baltic"
REGIONS = {
    "Baltic": {
        "bounds": {"North": 66, "South": 52, "West": 7, "East": 31},
        "projection": {"central_longitude": 20, "central_latitude": 60, "standard_parallels": (55, 65)},
        "ports": [
            ("Ust-Luga", "RU", 28.3, 59.7),
            ("Gdańsk", "PL", 18.65, 54.35),
            ("Primorsk", "RU", 28.6, 60.4),
            ("Saint Petersburg", "RU", 30.2, 59.93),
            ("Klaipėda", "LT", 21.1, 55.7),
            ("Szczecin-Świnoujście", "PL", 14.2, 53.6),
            ("Rostock", "DE", 12.1, 54.15),
            ("Gdynia", "PL", 18.55, 54.52),
            ("Porvoo", "FI", 25.65, 60.4),
            ("Riga", "LV", 24.1, 56.95),
        ],
    },
    "Black Sea": {
        "bounds": {"North": 47.2, "South": 40.5, "West": 27, "East": 42},
        "projection": {"central_longitude": 34.5, "central_latitude": 43.8, "standard_parallels": (41, 46)},
        "ports": [
            ("Constanța", "RO", 28.63, 44.16),
            ("Odessa", "UA", 30.74, 46.49),
            ("Novorossiysk", "RU", 37.94, 44.72),
            ("Batumi", "GE", 41.62, 41.64),
            ("Varna", "BG", 27.95, 43.20),
            ("Burgas", "BG", 27.47, 42.50),
            ("Samsun", "TR", 36.33, 41.28),
            ("Trabzon", "TR", 39.73, 41.0),
            ("Poti", "GE", 41.67, 42.15),
        ],
    },
}

# Time and processing
TIME_INDEX = 53  # center day for 7-day mean (3 before + day + 3 after)
DAYS_AVG = 7  # number of days to average
ICE_EDGE_PCT = 0.25  # 15% concentration = ice edge (standard metric)
SMOOTH_SIGMA = 1.5
# Set True to mask grid points on land (slower; avoids land/ocean ambiguity)
BUILD_LAND_MASK = True
# Print fraction of grid cells with valid data (helps spot missing data)
REPORT_DATA_COVERAGE = True


def partition_icec_by_region(icec, region):
    """Subset icec to region (lat/lon bounds)."""
    out = icec.where(
        (icec.lat >= region["South"]) & (icec.lat <= region["North"])
        & (icec.lon >= region["West"]) & (icec.lon <= region["East"])
    )
    return out


def build_land_mask(lon_2d, lat_2d):
    """Boolean mask True where (lon, lat) is on land (so we can set ice to NaN there)."""
    from cartopy.feature import NaturalEarthFeature
    land_feature = NaturalEarthFeature("physical", "land", "110m")
    geoms = list(land_feature.geometries())
    # Use only geometries that might intersect our bbox to speed up
    min_lon, max_lon = float(np.nanmin(lon_2d)), float(np.nanmax(lon_2d))
    min_lat, max_lat = float(np.nanmin(lat_2d)), float(np.nanmax(lat_2d))
    from shapely.geometry import box
    bbox = box(min_lon, min_lat, max_lon, max_lat)
    relevant = [g for g in geoms if g.intersects(bbox)]
    if not relevant:
        return np.zeros(lon_2d.shape, dtype=bool)
    union = unary_union(relevant)
    prepared = union  # unary_union may not be prepared; contains() still works
    shape = lon_2d.shape
    lon_flat = np.asarray(lon_2d).ravel()
    lat_flat = np.asarray(lat_2d).ravel()
    mask_flat = np.array([prepared.contains(Point(lon_flat[i], lat_flat[i])) for i in range(len(lon_flat))])
    return mask_flat.reshape(shape)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    region_config = REGIONS.get(REGION, REGIONS["Baltic"])
    bounds = region_config["bounds"]
    proj_params = region_config["projection"]
    ports = region_config.get("ports", [])

    ds = xr.open_dataset(os.path.join(DATA_DIR, "icec.day.mean.2026.nc"))
    icec = ds.icec
    icec = partition_icec_by_region(icec, bounds)

    # Subset coordinates for this region (slicing for smaller grid)
    lat = ds.lat.values
    lon = ds.lon.values
    lat_sel = np.where((lat >= bounds["South"]) & (lat <= bounds["North"]))[0]
    lon_sel = np.where((lon >= bounds["West"]) & (lon <= bounds["East"]))[0]
    if len(lat_sel) == 0 or len(lon_sel) == 0:
        lat_sel = np.arange(len(lat))
        lon_sel = np.arange(len(lon))
    lat_sub = lat[lat_sel]
    lon_sub = lon[lon_sel]
    icec_sub = icec.isel(lat=lat_sel, lon=lon_sel)

    # Time window: 7-day average centered on TIME_INDEX
    half = DAYS_AVG // 2
    time_idx_center = min(max(TIME_INDEX, half), icec_sub.sizes["time"] - 1 - half)
    time_slice = slice(time_idx_center - half, time_idx_center + half + 1)
    icec_avg = icec_sub.isel(time=time_slice).mean(dim="time")
    t_start = icec_sub.time.isel(time=time_slice.start)
    t_end = icec_sub.time.isel(time=time_slice.stop - 1)
    try:
        date_str = f"{t_start.dt.strftime('%Y-%m-%d').values} – {t_end.dt.strftime('%Y-%m-%d').values} ({DAYS_AVG}-day mean)"
    except Exception:
        date_str = f"{str(t_start.values)[:10]} – {str(t_end.values)[:10]} ({DAYS_AVG}-day mean)"

    # Data: 7-day mean (2D)
    data = np.asarray(icec_avg)
    lon_2d, lat_2d = np.meshgrid(lon_sub, lat_sub)

    # Land mask: set land to NaN so "no ice" is only over ocean (optional, slow)
    if BUILD_LAND_MASK:
        land = build_land_mask(lon_2d, lat_2d)
        data = np.where(land, np.nan, data)
    else:
        land = np.zeros_like(data, dtype=bool)

    # Ocean-only mask (existing NaNs in data)
    valid = ~np.isnan(data)
    n_valid, n_total = int(np.sum(valid)), data.size
    if REPORT_DATA_COVERAGE:
        pct = 100 * n_valid / n_total if n_total else 0
        print(f"Data coverage: {n_valid} / {n_total} grid cells ({pct:.1f}%) have valid ice concentration; rest are NaN (open water, land, or missing in file).")
        if n_valid == 0 and n_total > 0:
            print(f"  → This product has no ice data for the {REGION} region (typical for global products that only cover polar/high-latitude seas).")
    smoothed = np.full_like(data, np.nan)
    smoothed[valid] = gaussian_filter(
        np.where(valid, data, 0), sigma=SMOOTH_SIGMA, mode="constant", cval=0
    )[valid]
    smoothed[~valid] = np.nan

    # Climatology: 7-day mean for same day-of-year range (for overlay)
    try:
        ltm_path = os.path.join(DATA_DIR, "icec.day.mean.ltm.1991-2020.nc")
        ltm_ds = xr.open_dataset(ltm_path)
        # Map our 7-day window to LTM time indices (0-based day of year)
        doy_indices = icec_sub.time.dt.dayofyear.isel(time=time_slice).values
        doy_indices = np.clip(doy_indices - 1, 0, ltm_ds.sizes["time"] - 1)  # 0-based
        ltm_slice_7 = ltm_ds.icec.isel(time=doy_indices).mean(dim="time")
        ltm_icec = partition_icec_by_region(ltm_slice_7, bounds)
        ltm_sub = ltm_icec.isel(lat=lat_sel, lon=lon_sel).values
        ltm_sub = np.where(land, np.nan, ltm_sub)
        ltm_smooth = np.full_like(ltm_sub, np.nan)
        v = ~np.isnan(ltm_sub)
        ltm_smooth[v] = gaussian_filter(
            np.where(v, ltm_sub, 0), sigma=SMOOTH_SIGMA, mode="constant", cval=0
        )[v]
        has_ltm = True
    except Exception:
        has_ltm = False

    # Map: Lambert Conformal for selected region
    proj = ccrs.LambertConformal(**proj_params)
    fig, ax = plt.subplots(figsize=(11, 8), subplot_kw=dict(projection=proj))
    ax.set_extent([bounds["West"], bounds["East"], bounds["South"], bounds["North"]], crs=ccrs.PlateCarree())
    ax.set_facecolor("#ffffff")

    # Coastlines and land (nicer color)
    ax.coastlines(resolution="50m", linewidth=0.5)
    ax.add_feature(
        cfeature.NaturalEarthFeature("physical", "land", "50m"),
        facecolor="#e8e4d9", edgecolor="0.3", linewidth=0.3,
    )
    ax.add_feature(cfeature.BORDERS, edgecolor="0.4", linewidth=0.3)


    # Ice concentration fill
    levels = np.linspace(0, 1, 21)
    cf = ax.contourf(
        lon_2d, lat_2d, smoothed,
        transform=ccrs.PlateCarree(),
        cmap=ICE_CMAP,
        levels=levels,
        extend="max",
    )

    # Ice edge contour
    # Ice edge contour (use 0 for NaN so contour is continuous, not fragmented)
    contour_data = np.where(np.isnan(smoothed), 0.0, smoothed)
    ax.contour(
        lon_2d, lat_2d, contour_data,
        levels=[ICE_EDGE_PCT],
        transform=ccrs.PlateCarree(),
        colors="black", linewidths=1.5, linestyles="-",
    )

    # Climatology ice edge overlay (dashed)
    if has_ltm:
        contour_ltm = np.where(np.isnan(ltm_smooth), 0.0, ltm_smooth)
        ax.contour(
            lon_2d, lat_2d, contour_ltm,
            levels=[ICE_EDGE_PCT],
            transform=ccrs.PlateCarree(),
            colors="gray", linewidths=1.2, linestyles="--", alpha=0.9,
        )

    # Ice extent (area where concentration >= threshold) in km² for legend
    R_KM = 6371.0
    dlat = np.median(np.abs(np.diff(lat_sub))) if len(lat_sub) > 1 else 1.0
    dlon = np.median(np.abs(np.diff(lon_sub))) if len(lon_sub) > 1 else 1.0
    dlat_rad, dlon_rad = np.radians(dlat), np.radians(dlon)
    lat_rad = np.radians(lat_sub)
    area_km2 = (R_KM ** 2) * dlat_rad * dlon_rad * np.cos(lat_rad)[:, np.newaxis] * np.ones((len(lat_sub), len(lon_sub)))
    extent_km2_current = float(np.nansum(np.where(smoothed >= ICE_EDGE_PCT, area_km2, 0)))
    extent_km2_ltm = float(np.nansum(np.where(ltm_smooth >= ICE_EDGE_PCT, area_km2, 0))) if has_ltm else None

    # Ports (if defined for this region)
    if ports:
        try:
            from matplotlib.patheffects import withStroke
            path_effect = withStroke(linewidth=2, foreground="white")
        except Exception:
            path_effect = None
        lons = [p[2] for p in ports]
        lats = [p[3] for p in ports]
        ax.plot(lons, lats, "o", color="black", markersize=4, markeredgecolor="white", markeredgewidth=0.8, transform=ccrs.PlateCarree(), zorder=11)
        text_offset = 0.25
        port_kw = dict(transform=ccrs.PlateCarree(), fontsize=8, ha="left", va="center", zorder=10)
        if path_effect:
            port_kw["path_effects"] = [path_effect]
        for name, country, lon_p, lat_p in ports:
            ax.text(lon_p + text_offset, lat_p, f"{name} ({country})", **port_kw)

    # Colorbar
    cbar = fig.colorbar(cf, ax=ax, shrink=0.7, pad=0.06, fraction=0.04)
    cbar.set_label("Ice concentration (fraction)", fontsize=12, fontweight="medium")
    cbar.ax.tick_params(labelsize=11)
    cbar.set_ticks(np.linspace(0, 1, 11))

    ax.set_title(f"Sea ice concentration — {REGION} — {date_str}", fontsize=14, fontweight="medium", pad=10)
    edge_pct_label = f"{int(ICE_EDGE_PCT * 100)}%"
    extent_str = f"Current extent: {extent_km2_current:,.0f} km²"
    if has_ltm:
        extent_str += f"\nClimatology extent: {extent_km2_ltm:,.0f} km²"
    legend_lines = [f"Black line: {edge_pct_label} ice edge (current)", f"Dashed: {edge_pct_label} climatology (1991–2020)", extent_str] if has_ltm else [f"Black line: {edge_pct_label} ice edge", extent_str]
    ax.text(0.02, 0.02, "\n".join(legend_lines), transform=ax.transAxes, fontsize=8, va="bottom", ha="left", bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="0.4", alpha=0.92))

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f"sea_ice_{REGION}_{date_str}.png"), dpi=300, bbox_inches="tight")


if __name__ == "__main__":
    main()
