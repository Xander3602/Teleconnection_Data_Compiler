import os
from datetime import date
from math import floor, ceil
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mimg
import matplotlib.ticker as mticker
from matplotlib.transforms import blended_transform_factory

from paths import (
    DATA_DIR,
    WATERMARK_LOGO_PATH,
    output_dir_for,
)

# --- Edit these ---
YEARS_TO_PLOT = [2026, 2023, 2018, 2014, 2009, 2006, 2002, 1997]
CURRENT_YEAR = 2026
ENSO_REGION = "nino34"  # used only when PLOT_ALL_REGIONS is False
# Set to True to generate all 4 ENSO region plots into a date-stamped folder; False = single region only
PLOT_ALL_REGIONS = True
ALL_REGIONS = ["nino12", "nino3", "nino34", "nino4"]

WATERMARK_ALPHA = 0.12

REGION_LABELS = {"nino12": "Niño 1+2", "nino3": "Niño 3", "nino34": "Niño 3.4", "nino4": "Niño 4"}
LA_NINA_THRESHOLD = -0.5
EL_NINO_THRESHOLD = 0.5


def load_enso_data():
    """Load and prepare ENSO CSV; returns DataFrame with day_of_year and x."""
    df = pd.read_csv(os.path.join(DATA_DIR, "enso.csv"))
    df["month"] = df["month"].astype(int)
    df["day"] = df["day"].astype(int)
    df["year"] = df["year"].astype(int)
    dates = pd.to_datetime(df[["year", "month", "day"]])
    df["day_of_year"] = dates.dt.dayofyear
    days_in_year = dates.dt.is_leap_year.map({True: 366, False: 365})
    df["x"] = 1 + (df["day_of_year"] - 1) / days_in_year * 11
    df = df.sort_values(["year", "month", "day"]).reset_index(drop=True)
    return df


def main():
    df = load_enso_data()
    output_dir = os.path.join(output_dir_for("enso"), f"enso_plots_{date.today().isoformat()}")
    os.makedirs(output_dir, exist_ok=True)
    if PLOT_ALL_REGIONS:
        for reg in ALL_REGIONS:
            build_and_save_enso_plot(
                df, reg, output_dir,
                YEARS_TO_PLOT, CURRENT_YEAR,
                WATERMARK_LOGO_PATH, WATERMARK_ALPHA,
            )
        print(f"Saved 4 plots to folder: {output_dir}")
    else:
        build_and_save_enso_plot(
            df, ENSO_REGION, output_dir,
            YEARS_TO_PLOT, CURRENT_YEAR,
            WATERMARK_LOGO_PATH, WATERMARK_ALPHA,
        )
        print(f"Saved 1 plot to folder: {output_dir}")


if __name__ == "__main__":
    main()


def build_and_save_enso_plot(
    data,
    region,
    output_dir,
    years_to_plot,
    current_year,
    watermark_path,
    watermark_alpha,
):
    """Build one ENSO plot for the given region and save PNG + SVG into output_dir."""
    region_col = f"{region}_ssta"
    if region_col not in data.columns:
        raise ValueError(f"Column {region_col} not in data. Choose one of: {ALL_REGIONS}")
    region_label = REGION_LABELS.get(region, region)

    years = sorted(y for y in data["year"].unique() if y in years_to_plot)
    other_years = [y for y in years if y != current_year]
    cmap = plt.cm.viridis
    fig, ax = plt.subplots(figsize=(11, 6), facecolor="white")
    ax.set_facecolor("white")

    plot_data = data[data["year"].isin(years_to_plot)]
    y_min, y_max = plot_data[region_col].min(), plot_data[region_col].max()
    y_pad = max((y_max - y_min) * 0.08, 0.15)
    y_lo = min(y_min - y_pad, LA_NINA_THRESHOLD - 0.05)
    y_hi = max(y_max + y_pad, EL_NINO_THRESHOLD + 0.05)
    y_lo = 0.5 * floor(y_lo / 0.5)
    y_hi = 0.5 * ceil(y_hi / 0.5)
    ax.set_xlim(1, 12)
    ax.set_ylim(y_lo, y_hi)

    ax.axhspan(LA_NINA_THRESHOLD, EL_NINO_THRESHOLD, facecolor="#e8ecf0", alpha=0.4, zorder=0)
    ax.set_axisbelow(True)

    for year in years:
        subset = data[data["year"] == year]
        if year == current_year:
            ax.plot(
                subset["x"], subset[region_col],
                color="black", linestyle="-", linewidth=2.5, label=f"{year} (current)",
                zorder=2, solid_capstyle="round", solid_joinstyle="round",
            )
        else:
            j = other_years.index(year)
            color = cmap(j / max(len(other_years) - 1, 1))
            ax.plot(
                subset["x"], subset[region_col],
                color=color, linestyle="--", alpha=0.8, label=str(year),
                zorder=2, solid_capstyle="round", solid_joinstyle="round",
            )

    ax.axhline(0, color="gray", linestyle="--", linewidth=0.9, alpha=0.8, zorder=1)
    ax.axhline(EL_NINO_THRESHOLD, color="#c0392b", linestyle=":", linewidth=1.2, alpha=0.9, zorder=1)
    ax.axhline(LA_NINA_THRESHOLD, color="#2980b9", linestyle=":", linewidth=1.2, alpha=0.9, zorder=1)
    trans = blended_transform_factory(ax.transAxes, ax.transData)
    ax.text(1.02, EL_NINO_THRESHOLD, " El Niño (≥0.5°C)", va="center", ha="left", fontsize=9, fontweight="500", color="#c0392b", alpha=0.9, transform=trans)
    ax.text(1.02, LA_NINA_THRESHOLD, " La Niña (≤-0.5°C)", va="center", ha="left", fontsize=9, fontweight="500", color="#2980b9", alpha=0.9, transform=trans)

    ax.yaxis.set_major_locator(mticker.MultipleLocator(0.5))
    ax.grid(True, axis="y", linestyle="-", linewidth=0.45, alpha=0.35)
    ax.set_axisbelow(True)

    label_color = "#2c3e50"
    ax.set_xlabel("Month", fontsize=12, fontweight="600", color=label_color, labelpad=8)
    ax.set_ylabel(f"{region_label} SSTA (°C)", fontsize=12, fontweight="600", color=label_color, labelpad=8)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        fontsize=11, fontweight="500", color=label_color,
    )
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))
    ax.tick_params(axis="both", which="major", labelsize=11, length=5, width=1, color=label_color, labelcolor=label_color, pad=5, direction="out")
    for spine_name in ["top", "right", "bottom", "left"]:
        ax.spines[spine_name].set_color("#4a5568")
        ax.spines[spine_name].set_linewidth(0.8)
    ax.spines["top"].set_visible(True)
    ax.spines["right"].set_visible(True)

    ax.set_title(f"ENSO {region_label} — Sea Surface Temperature Anomaly by Month", fontsize=13, fontweight="600", pad=10)
    handles, labels = ax.get_legend_handles_labels()
    current_label = f"{current_year} (current)"
    if current_label in labels:
        idx = labels.index(current_label)
        handles = [handles[idx]] + [h for i, h in enumerate(handles) if i != idx]
        labels = [labels[idx]] + [l for i, l in enumerate(labels) if i != idx]
    leg = ax.legend(handles, labels, loc="upper left", frameon=True, framealpha=0.95, edgecolor="0.85", fontsize=9, ncol=2, columnspacing=1.2, handlelength=2.2)
    leg.set_zorder(3)
    # Reserve bottom margin so caption and x-axis label don't overlap tick labels
    plt.tight_layout(pad=1.0, rect=(0, 0.05, 1, 1))
    fig.text(0.47, 0.055, "Created by Aura Commodities - 2026", ha="center", fontsize=9, color="#64748b", style="italic")

    if os.path.isfile(watermark_path):
        logo = mimg.imread(watermark_path)
        if logo.shape[-1] == 4:
            logo = logo.copy()
            logo[..., 3] *= watermark_alpha
            alpha = None
        else:
            alpha = watermark_alpha
        pos = ax.get_position()
        axes_aspect = (pos.width * fig.get_figwidth()) / (pos.height * fig.get_figheight())
        margin = 0.22
        height_axes = 1 - 2 * margin
        width_axes = height_axes / axes_aspect
        extent_axes = [0.5 - width_axes / 2, 0.5 + width_axes / 2, margin, 1 - margin]
        ax.imshow(logo, extent=extent_axes, aspect="equal", alpha=alpha, zorder=0, interpolation="bilinear", transform=ax.transAxes)

    base = os.path.join(output_dir, f"enso_{region}")
    fig.savefig(f"{base}.png", dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
    fig.savefig(f"{base}.svg", format="svg", bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)
