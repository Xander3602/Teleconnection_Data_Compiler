
import pandas as pd
import os
import datetime
import matplotlib.pyplot as plt

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
df = pd.read_csv(os.path.join(_PROJECT_ROOT, "data", "epo.reanalysis.1948-present.csv"))

OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "output", "epo")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Years to compare (edit this list to add/remove years)
YEARS_TO_PLOT = [2009, 2023, 2026]
CURRENT_YEAR = datetime.date.today().year

# Month range to plot: (start_month, end_month) inclusive, or None for full year
# e.g. (2, 4) for February through April
MONTH_RANGE = (2, 4)  # e.g. (2, 4) for Feb–Apr only

fig, ax = plt.subplots(figsize=(12, 5))

for year in YEARS_TO_PLOT:
    df_year = df[df["year"] == year].copy()
    if df_year.empty:
        print(f"No data for year {year}, skipping.")
        continue
    if MONTH_RANGE is not None:
        start_mo, end_mo = MONTH_RANGE
        df_year = df_year[(df_year["month"] >= start_mo) & (df_year["month"] <= end_mo)]
        if df_year.empty:
            continue
    # Use day-of-year for x so all years align on the same calendar
    df_year["day_of_year"] = pd.to_datetime(
        df_year[["year", "month", "day"]]
    ).dt.dayofyear
    is_current = year == CURRENT_YEAR
    ax.plot(
        df_year["day_of_year"],
        df_year["epo index (m)"],
        label=str(year),
        color="black" if is_current else None,
        linestyle="-" if is_current else "--",
        linewidth=2 if is_current else 1.5,
    )

ax.set_xlabel("Date")
ax.set_ylabel("EPO index (m)")
title = "EPO index comparison by year"
if MONTH_RANGE is not None:
    start_mo, end_mo = MONTH_RANGE
    months = [datetime.date(2000, m, 1).strftime("%B") for m in range(start_mo, end_mo + 1)]
    title += f" ({' – '.join(months)})"
ax.set_title(title)
ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
ax.axhline(0, color="gray", linestyle="--", linewidth=0.8)
ax.grid(True, alpha=0.3)

# X-axis: day-of-year ticks at 1st and 15th of each month, with date labels
ref_year = 2023  # non-leap year for consistent day-of-year
months_to_show = range(MONTH_RANGE[0], MONTH_RANGE[1] + 1) if MONTH_RANGE else range(1, 13)
ticks_doy = []
tick_labels = []
for month in months_to_show:
    for day in [1, 15]:
        try:
            d = datetime.date(ref_year, month, day)
            ticks_doy.append(d.timetuple().tm_yday)
            tick_labels.append(f"{d.strftime('%b')} {d.day}")
        except ValueError:
            pass
ax.set_xticks(ticks_doy)
ax.set_xticklabels(tick_labels, rotation=45, ha="right")
if MONTH_RANGE is not None:
    start_doy = datetime.date(ref_year, MONTH_RANGE[0], 1).timetuple().tm_yday
    end_doy = datetime.date(ref_year, MONTH_RANGE[1] + 1, 1).timetuple().tm_yday - 1
    ax.set_xlim(start_doy, end_doy)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "epo_comparison.png"), dpi=300, bbox_inches="tight")
plt.show()
