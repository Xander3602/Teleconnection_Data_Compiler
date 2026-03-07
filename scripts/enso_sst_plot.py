import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import calendar
import pandas as pd
import os


_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
ENSO_DATA_DIR = os.path.join(DATA_DIR, "enso")
OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "output", "enso")


def add_aura_watermarks(fig, ax, logo_path=None):
    """Add 'AURA COMMODITIES LTD' text watermark and Aura logo in top-right corner."""
    ax.text(
        0.5, 0.5, "AURA COMMODITIES LTD",
        transform=ax.transAxes,
        fontsize=20,
        fontweight="bold",
        color="gray",
        alpha=0.14,
        ha="center",
        va="center",
        rotation=30,
        zorder=0.5,
    )


def read_ssta_data(file_path):
    ds = xr.open_dataset(file_path)
    sst_mean = ds["ssta"].mean(dim=["latitude", "longitude"])
    sst_plot = sst_mean.squeeze("forecast_reference_time")
    lead_months = sst_plot.coords["forecastMonth"].values
    return sst_plot, lead_months


def plot_sst_anomaly(
    ssta_data,
    lead_months,
    *,
    init_month=3,
    current_year=None,
    analog_years=None,
    enso_region="nino34",
    logo_path=None,
):
    months_plot = np.arange(1, init_month + 6)
    n_backfill = init_month - 1

    fig, ax = plt.subplots(figsize=(8, 4))

    if analog_years:
        analog_colors = ["forestgreen", "darkorange", "purple", "crimson", "teal"]
        for j, year in enumerate(analog_years):
            enso = get_enso_data_monthly_by_year(year, enso_region, "ssta")
            y_analog = [enso.get(m, np.nan) for m in months_plot]
            ax.plot(
                months_plot,
                y_analog,
                color=analog_colors[j % len(analog_colors)],
                linewidth=2,
                linestyle="--",
                alpha=0.9,
                label=f"{year}",
            )

    x_forecast = (lead_months + (init_month - 1)).tolist()
    for i in range(ssta_data.sizes["number"]):
        ax.plot(
            x_forecast,
            ssta_data.isel(number=i),
            color="gray",
            alpha=0.45,
            linewidth=0.5,
        )
    p10 = ssta_data.quantile(0.10, dim="number").squeeze().values
    p90 = ssta_data.quantile(0.90, dim="number").squeeze().values
    ax.fill_between(x_forecast, p10, p90, color="darkblue", alpha=0.22, zorder=0)
    ax.plot(
        x_forecast,
        ssta_data.mean(dim="number"),
        color="darkblue",
        linewidth=2,
        label="Ensemble mean",
    )

    if current_year is not None and n_backfill > 0:
        current_enso = get_enso_data_monthly_by_year(current_year, enso_region, "ssta")
        y_obs = [current_enso.get(m, np.nan) for m in range(1, init_month)]
        x_obs = list(range(1, init_month))
        ax.plot(
            x_obs,
            y_obs,
            color="blue",
            linewidth=2,
            linestyle="-",
            label=f"{current_year} (observed)",
        )
        ax.axvline(x=init_month, color="k", linestyle=":", alpha=0.4)

    ax.set_xticks(months_plot)
    ax.set_xticklabels([calendar.month_abbr[m] for m in months_plot])
    ax.set_xlabel("")
    ax.set_ylabel("SST Anomaly (°C)")
    ax.set_title(
        f"Domain-mean SST Anomaly · 51 members Initialization: {calendar.month_name[init_month]} {current_year or '2026'}"
    )
    handles, labels = ax.get_legend_handles_labels()
    patch_1090 = mpatches.Patch(facecolor="darkblue", alpha=0.22, edgecolor="none")
    ax.legend(
        handles=[patch_1090] + handles,
        labels=["10–90th %"] + labels,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.08),
        ncol=4,
        frameon=True,
    )
    ax.grid(True, alpha=0.3)
    add_aura_watermarks(fig, ax, logo_path=logo_path)
    plt.tight_layout(rect=[0, 0.06, 1, 1])
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "sst_anomaly.png")
    plt.savefig(out_path)
    plt.close()
    return out_path


def get_enso_data_monthly_by_year(year, region, temperature_variable):
    if region not in ["nino12", "nino3", "nino34", "nino4"]:
        raise ValueError(f"Invalid region: {region}")
    if temperature_variable not in ["ssta", "sst"]:
        raise ValueError(f"Invalid temperature variable: {temperature_variable}")

    variable_name = f"{region}_{temperature_variable}"
    enso_csv = os.path.join(DATA_DIR, "enso.csv")
    df = pd.read_csv(enso_csv)
    enso_data = df[df["year"] == year]
    enso_data_by_month = enso_data.groupby("month").mean()
    enso_data_by_month = enso_data_by_month.round(3)
    enso_data_by_month = enso_data_by_month[variable_name]
    enso_data_by_month = enso_data_by_month.to_dict()
    return enso_data_by_month


if __name__ == "__main__":
    ssta_path = os.path.join(ENSO_DATA_DIR, "ssta_2026_03.nc")
    if not os.path.isfile(ssta_path):
        raise FileNotFoundError(
            f"ENSO SST anomaly NetCDF not found: {ssta_path}. "
            "Run scripts/cdsapi_sst.py first to download it (requires CDS API key)."
        )
    ssta_data, lead_months = read_ssta_data(ssta_path)
    out = plot_sst_anomaly(
        ssta_data,
        lead_months,
        init_month=3,
        current_year=2026,
        analog_years=[2023, 2002, 1997, 2015, 1982],
        enso_region="nino34",
    )
    print(f"Saved: {out}")
