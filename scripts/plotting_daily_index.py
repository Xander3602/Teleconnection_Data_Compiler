"""
Plot daily index data (e.g. AAO, NAO) by year with selected years overlaid.
Expects CSV with columns: year, month, day, and one value column (configurable).
"""
import os
from datetime import date
from math import floor, ceil
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mimg
import matplotlib.ticker as mticker
from matplotlib.transforms import blended_transform_factory

from paths import DATA_DIR, WATERMARK_LOGO_PATH, output_dir_for

# --- Edit these ---
INPUT_CSV = os.path.join(DATA_DIR, "aao.csv")
VALUE_COLUMN = "aao"  # column name for the index to plot
PLOT_TITLE = "AAO — Antarctic Oscillation Index"
Y_AXIS_LABEL = "AAO index"

YEARS_TO_PLOT = [2026, 2025, 2023, 2009, 2008, 2001, 1997]
CURRENT_YEAR = 2026

# Show only a span of months to declutter: (start_month, end_month) inclusive, 1=Jan, 12=Dec.
# Use (1, 12) for full year. Example: (1, 4) = Jan–Apr, (6, 9) = Jun–Sep.
MONTH_RANGE = (1, 12)

# Optional: smooth lines with N-day rolling mean (within each year). Set to None for raw daily.
ROLLING_DAYS = 7

# Optional: horizontal reference lines (value, color, linestyle, label)
# Use None for no line. For a shaded neutral band, set REFERENCE_BAND = (low, high).
REFERENCE_LINES = [
    (0.0, "gray", "--", None),
    (1.0, "#2ecc71", ":", None),
    (-1.0, "#e74c3c", ":", None),
]
REFERENCE_BAND = None  # e.g. (-0.5, 0.5) for neutral, or None

WATERMARK_ALPHA = 0.12

# CSV column names (if your file uses different names, change here)
COL_YEAR = "year"
COL_MONTH = "month"
COL_DAY = "day"


def load_and_prepare_daily(csv_path, value_col, col_year, col_month, col_day):
    """Load CSV and compute day-of-year and x position (1–12 for months)."""
    df = pd.read_csv(csv_path)
    df[col_month] = df[col_month].astype(int)
    df[col_day] = df[col_day].astype(int)
    df[col_year] = df[col_year].astype(int)
    dates = pd.to_datetime(df[[col_year, col_month, col_day]])
    df["day_of_year"] = dates.dt.dayofyear
    days_in_year = dates.dt.is_leap_year.map({True: 366, False: 365})
    df["x"] = 1 + (df["day_of_year"] - 1) / days_in_year * 11
    df = df.sort_values([col_year, col_month, col_day]).reset_index(drop=True)
    if value_col not in df.columns:
        raise ValueError(f"Column '{value_col}' not in CSV. Available: {list(df.columns)}")
    return df


def build_and_save_plot(
    data,
    value_col,
    output_dir,
    years_to_plot,
    current_year,
    plot_title,
    y_label,
    reference_lines,
    reference_band,
    watermark_path,
    watermark_alpha,
    col_year,
    col_month,
    month_range,
    rolling_days,
):
    """Build one daily-index plot and save PNG + SVG."""
    month_start, month_end = month_range
    data = data[data[col_month].between(month_start, month_end)].copy()
    if data.empty:
        raise ValueError(f"No data in month range {month_range}")

    if rolling_days is not None and rolling_days > 1:
        data["_plot_val"] = (
            data.groupby(col_year)[value_col]
            .transform(lambda s: s.rolling(rolling_days, min_periods=1).mean())
        )
    else:
        data["_plot_val"] = data[value_col]

    years = sorted(y for y in data[col_year].unique() if y in years_to_plot)
    other_years = [y for y in years if y != current_year]
    cmap = plt.cm.viridis
    fig, ax = plt.subplots(figsize=(16, 6), facecolor="white")
    ax.set_facecolor("white")

    plot_data = data[data[col_year].isin(years_to_plot)]
    y_min, y_max = plot_data["_plot_val"].min(), plot_data["_plot_val"].max()
    y_pad = max((y_max - y_min) * 0.08, 0.15)
    y_lo = y_min - y_pad
    y_hi = y_max + y_pad
    if reference_lines:
        ref_vals = [r[0] for r in reference_lines if r[0] is not None]
        if ref_vals:
            y_lo = min(y_lo, min(ref_vals) - 0.2)
            y_hi = max(y_hi, max(ref_vals) + 0.2)
    if reference_band:
        y_lo = min(y_lo, reference_band[0] - 0.1)
        y_hi = max(y_hi, reference_band[1] + 0.1)
    y_lo = 0.5 * floor(y_lo / 0.5)
    y_hi = 0.5 * ceil(y_hi / 0.5)
    ax.set_xlim(month_start, month_end + 1)
    ax.set_ylim(y_lo, y_hi)

    if reference_band is not None:
        ax.axhspan(
            reference_band[0], reference_band[1],
            facecolor="#e8ecf0", alpha=0.4, zorder=0,
        )
    ax.set_axisbelow(True)

    for year in years:
        subset = data[data[col_year] == year]
        if year == current_year:
            ax.plot(
                subset["x"], subset["_plot_val"],
                color="black", linestyle="-", linewidth=2.5, label=f"{year} (current)",
                zorder=2, solid_capstyle="round", solid_joinstyle="round",
            )
        else:
            j = other_years.index(year)
            color = cmap(j / max(len(other_years) - 1, 1))
            ax.plot(
                subset["x"], subset["_plot_val"],
                color=color, linestyle="--", alpha=0.8, label=str(year),
                zorder=2, solid_capstyle="round", solid_joinstyle="round",
            )

    for item in reference_lines or []:
        if item is None or item[0] is None:
            continue
        val, color, ls, label = item[0], item[1], item[2], item[3] if len(item) > 3 else None
        ax.axhline(val, color=color, linestyle=ls, linewidth=1.2, alpha=0.9, zorder=1)
        if label:
            trans = blended_transform_factory(ax.transAxes, ax.transData)
            ax.text(1.02, val, f" {label}", va="center", ha="left", fontsize=9, fontweight="500", color=color, alpha=0.9, transform=trans)

    ax.yaxis.set_major_locator(mticker.MultipleLocator(0.5))
    ax.grid(True, axis="y", linestyle="-", linewidth=0.45, alpha=0.35)
    ax.set_axisbelow(True)

    label_color = "#2c3e50"
    ax.set_xlabel("Month", fontsize=12, fontweight="600", color=label_color, labelpad=8)
    ax.set_ylabel(y_label, fontsize=12, fontweight="600", color=label_color, labelpad=8)
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    ax.set_xticks(range(month_start, month_end + 1))
    ax.set_xticklabels(
        [month_names[m - 1] for m in range(month_start, month_end + 1)],
        fontsize=11, fontweight="500", color=label_color,
    )
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))
    ax.tick_params(axis="both", which="major", labelsize=11, length=5, width=1, color=label_color, labelcolor=label_color, pad=5, direction="out")
    for spine_name in ["top", "right", "bottom", "left"]:
        ax.spines[spine_name].set_color("#4a5568")
        ax.spines[spine_name].set_linewidth(0.8)
    ax.spines["top"].set_visible(True)
    ax.spines["right"].set_visible(True)

    span_label = f" ({month_names[month_start - 1]}–{month_names[month_end - 1]})" if (month_start, month_end) != (1, 12) else ""
    smooth_label = f" ({rolling_days}-day mean)" if rolling_days and rolling_days > 1 else ""
    ax.set_title(plot_title + " — by Month" + span_label + smooth_label, fontsize=13, fontweight="600", pad=10)
    handles, labels = ax.get_legend_handles_labels()
    current_label = f"{current_year} (current)"
    if current_label in labels:
        idx = labels.index(current_label)
        handles = [handles[idx]] + [h for i, h in enumerate(handles) if i != idx]
        labels = [labels[idx]] + [l for i, l in enumerate(labels) if i != idx]
    leg = ax.legend(handles, labels, loc="upper left", frameon=True, framealpha=0.95, edgecolor="0.85", fontsize=9, ncol=2, columnspacing=1.2, handlelength=2.2)
    leg.set_zorder(3)
    plt.tight_layout(pad=0.5)
    # Expand axes to use most of figure width and height (reduce white space left/right)
    fig.subplots_adjust(left=0.06, right=0.96, top=0.90, bottom=0.11)
    fig.text(0.39, 0.024, "Created by Aura Commodities - 2026", ha="center", fontsize=9, color="#64748b", style="italic")

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

    base_name = os.path.splitext(os.path.basename(INPUT_CSV))[0]
    base = os.path.join(output_dir, base_name)
    fig.savefig(f"{base}.png", dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
    fig.savefig(f"{base}.svg", format="svg", bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)


def main():
    df = load_and_prepare_daily(INPUT_CSV, VALUE_COLUMN, COL_YEAR, COL_MONTH, COL_DAY)
    output_dir = os.path.join(output_dir_for("daily_index"), f"{os.path.splitext(os.path.basename(INPUT_CSV))[0]}_plots_{date.today().isoformat()}")
    os.makedirs(output_dir, exist_ok=True)
    build_and_save_plot(
        df, VALUE_COLUMN, output_dir,
        YEARS_TO_PLOT, CURRENT_YEAR,
        PLOT_TITLE, Y_AXIS_LABEL,
        REFERENCE_LINES, REFERENCE_BAND,
        WATERMARK_LOGO_PATH, WATERMARK_ALPHA,
        COL_YEAR, COL_MONTH,
        MONTH_RANGE, ROLLING_DAYS,
    )
    print(f"Saved plot to folder: {output_dir}")


if __name__ == "__main__":
    main()
