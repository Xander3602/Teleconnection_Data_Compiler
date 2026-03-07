import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import numpy as np
from scipy.interpolate import make_interp_spline

from paths import DATA_DIR, PROJECT_ROOT, WATERMARK_LOGO_PATH, output_dir_for

# Alias for compatibility with variable name used in this script
WATERMARK_PATH = WATERMARK_LOGO_PATH

# Date range to plot (None = use full range from data)
# Examples: (1990, 2020), (2000, None) for 2000 to latest, (None, 2010) for start to 2010
START_YEAR = 1991  # e.g. 1990
END_YEAR = 2026   # e.g. 2024

# Points to highlight: list of (year, month) tuples
# Month can be: 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
#               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
HIGHLIGHT_POINTS = [
    # (1997, 'Jun'),   # Strong El Niño year
    # (2006, 'Jun'),   # La Niña transition
    # (2009, 'Jun'),   # Cool phase
    # (2014, 'Jun'),   # Strong negative
    # (2018, 'Jun'),   # Recent negative peak
    # (2023, 'Jun'),   # Most recent data
]

# Chart settings
FIGURE_SIZE = (16, 7)
TITLE = "Indian Ocean Dipole (IOD) Index - Monthly (DMI, JMA)"
POSITIVE_COLOR = '#E63946'  # Red for positive (warm phase)
NEGATIVE_COLOR = '#457B9D'  # Blue for negative (cool phase)
HIGHLIGHT_COLOR = '#FFD700'  # Gold for highlighted points
HIGHLIGHT_MARKER_SIZE = 120

# Data and watermark paths (relative to project root: data/ and assets/)
DATA_CSV = os.path.join(DATA_DIR, 'JMA_IOD_Data_long.csv')
WATERMARK_ALPHA = 0.15  # Transparency (0 = invisible, 1 = fully opaque)
WATERMARK_SCALE = 0.25  # Size scale relative to original image

# =============================================================================
# DATA LOADING AND PROCESSING
# =============================================================================

MONTH_COLS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

MONTH_TO_NUM = {month: i+1 for i, month in enumerate(MONTH_COLS)}

def load_pdo_data_monthly(filepath=None, start_year=None, end_year=None):
    """Load IOD/DMI data from JMA long-format CSV and return monthly time series.
    Optionally filter by start_year and/or end_year (inclusive).
    """
    if filepath is None:
        filepath = DATA_CSV
    if start_year is None:
        start_year = START_YEAR
    if end_year is None:
        end_year = END_YEAR
    df = pd.read_csv(filepath)
    # JMA_IOD_Data_long.csv has: year, month, DMI index
    df = df.rename(columns={'year': 'Year', 'month': 'Month_Num'})
    # Drop sentinel values if present
    dmi_col = 'DMI index'
    df = df[df[dmi_col] != 99.9].copy()
    df['Date'] = pd.to_datetime({'year': df['Year'], 'month': df['Month_Num'], 'day': 1})
    # Chart code expects 'PDO' column for values
    df['PDO'] = df[dmi_col].astype(float)
    # Apply date range filter
    if start_year is not None:
        df = df[df['Year'] >= start_year]
    if end_year is not None:
        df = df[df['Year'] <= end_year]
    df = df.sort_values('Date').reset_index(drop=True)
    return df

def create_pdo_area_chart(df, highlight_points=None, save_path=None):
    """
    Create an area chart of monthly PDO values with color coding.
    
    Parameters:
    -----------
    df : pandas DataFrame
        DataFrame containing Date and PDO columns (monthly data)
    highlight_points : list of tuples
        List of (year, month) tuples to highlight on the chart
        e.g., [(1997, 'Jun'), (2008, 'Jan')]
    save_path : str, optional
        Path to save the figure. If None, displays interactively.
    """
    if highlight_points is None:
        highlight_points = []
    
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    
    dates = df['Date'].values
    pdo_values = df['PDO'].values
    
    # Convert dates to numeric for interpolation
    dates_numeric = mdates.date2num(dates)
    
    # Create smooth interpolation (increase points for smoother curve)
    num_smooth_points = len(dates) * 5  # 5x more points for smoothness
    dates_smooth = np.linspace(dates_numeric.min(), dates_numeric.max(), num_smooth_points)
    
    # Use cubic spline interpolation for smooth curves
    spline = make_interp_spline(dates_numeric, pdo_values, k=3)
    pdo_smooth = spline(dates_smooth)
    
    # Convert smooth dates back to datetime for plotting
    dates_smooth_dt = mdates.num2date(dates_smooth)
    
    # Create arrays for positive and negative values (for separate coloring)
    positive_values = np.where(pdo_smooth > 0, pdo_smooth, 0)
    negative_values = np.where(pdo_smooth < 0, pdo_smooth, 0)
    
    # Plot positive values (red) - fill from 0 to positive
    ax.fill_between(dates_smooth_dt, 0, positive_values,
                    color=POSITIVE_COLOR, alpha=0.7,
                    label='Positive IOD (Warm Phase)')
    # Plot negative values (blue) - fill from negative to 0
    ax.fill_between(dates_smooth_dt, negative_values, 0,
                    color=NEGATIVE_COLOR, alpha=0.7,
                    label='Negative IOD (Cool Phase)')
    
    # Plot the smooth line on top
    ax.plot(dates_smooth_dt, pdo_smooth, color='black', linewidth=0.8, alpha=0.6)
    
    # Add zero line
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1.5)
    
    # Highlight specific points (year, month)
    if highlight_points:
        for year, month in highlight_points:
            # Find the matching row
            month_num = MONTH_TO_NUM.get(month)
            if month_num is None:
                print(f"Warning: Invalid month '{month}' - skipping")
                continue
                
            mask = (df['Year'] == year) & (df['Month_Num'] == month_num)
            point_data = df[mask]
            
            if point_data.empty:
                print(f"Warning: No data for {month} {year} - skipping")
                continue
            
            point_date = point_data['Date'].values[0]
            point_value = point_data['PDO'].values[0]
            
            # Add scatter point
            ax.scatter(point_date, point_value, 
                       s=HIGHLIGHT_MARKER_SIZE, c=HIGHLIGHT_COLOR, 
                       edgecolors='black', linewidths=1.5, 
                       zorder=5)
            
            # Vertical dashed line
            ax.axvline(x=point_date, color='gray', linestyle='--', 
                       alpha=0.4, linewidth=1)
            
            # Label with month/year and value
            y_offset = 15 if point_value >= 0 else -15
            va = 'bottom' if point_value >= 0 else 'top'
            ax.annotate(f'{month} {year}\n({point_value:.2f})', 
                        xy=(point_date, point_value), 
                        xytext=(0, y_offset),
                        textcoords='offset points',
                        ha='center', va=va,
                        fontsize=8, fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.3', 
                                  facecolor='white', 
                                  edgecolor='gray', 
                                  alpha=0.9))
    
    # Create subtitle with highlighted years
    if highlight_points:
        highlighted_years = sorted(set(year for year, month in highlight_points))
        subtitle = f"Highlighted Years: {', '.join(str(y) for y in highlighted_years)}"
    else:
        subtitle = ""
    
    # Customize the chart
    ax.set_xlabel('Date', fontsize=14, fontweight='bold')
    ax.set_ylabel('DMI Index', fontsize=14, fontweight='bold')
    
    # Add main title and subtitle with proper spacing
    fig.suptitle(TITLE, fontsize=18, fontweight='bold', y=0.98)
    if subtitle:
        ax.set_title(subtitle, fontsize=11, style='italic', color='#555555', pad=10)
    
    # Make chart outline (spines) thicker
    for spine in ax.spines.values():
        spine.set_linewidth(2.0)
    
    # Format x-axis for dates
    ax.xaxis.set_major_locator(mdates.YearLocator(5))  # Major tick every 5 years
    ax.xaxis.set_minor_locator(mdates.YearLocator(1))  # Minor tick every year
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.tick_params(axis='x', rotation=45, width=2, length=6)
    ax.tick_params(axis='y', width=2, length=6)
    
    # Add grid
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # Add legend (without highlighted points entry)
    ax.legend(loc='upper right', framealpha=0.9)
    
    # Set y-axis limits with some padding
    y_min, y_max = pdo_smooth.min(), pdo_smooth.max()
    y_padding = (y_max - y_min) * 0.15
    ax.set_ylim(y_min - y_padding, y_max + y_padding)
    
    # Add watermark
    try:
        logo = mpimg.imread(WATERMARK_PATH)
        # Create an OffsetImage with transparency
        imagebox = OffsetImage(logo, zoom=WATERMARK_SCALE, alpha=WATERMARK_ALPHA)
        # Position watermark in center of the plot
        ab = AnnotationBbox(imagebox, (0.5, 0.5), frameon=False,
                            xycoords='axes fraction', boxcoords='axes fraction')
        ax.add_artist(ab)
    except FileNotFoundError:
        print(f"Warning: Watermark image not found at '{WATERMARK_PATH}'")
    
    plt.tight_layout(rect=[0, 0, 1, 0.95])  # Leave room for suptitle
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Chart saved to: {save_path}")
    
    plt.show()
    
    return fig, ax

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Load the data (JMA IOD long format)
    print("Loading IOD/DMI monthly data...")
    pdo_df = load_pdo_data_monthly()
    # Month name for summary (Month_Num is 1-12)
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    pdo_df['Month'] = pdo_df['Month_Num'].map(lambda m: month_names[m - 1])
    # Display summary
    print(f"\nData range: {pdo_df['Date'].min().strftime('%b %Y')} - {pdo_df['Date'].max().strftime('%b %Y')}")
    print(f"Total months: {len(pdo_df)}")
    print(f"DMI range: {pdo_df['PDO'].min():.2f} to {pdo_df['PDO'].max():.2f}")
    max_row = pdo_df.loc[pdo_df['PDO'].idxmax()]
    min_row = pdo_df.loc[pdo_df['PDO'].idxmin()]
    print(f"\nMost positive: {max_row['Month']} {int(max_row['Year'])} ({max_row['PDO']:.2f})")
    print(f"Most negative: {min_row['Month']} {int(min_row['Year'])} ({min_row['PDO']:.2f})")
    print(f"\nHighlighting points: {HIGHLIGHT_POINTS}")
    print("Creating chart...")
    _iod_out = os.path.join(output_dir_for("iod"), "iod_area_chart.png")
    os.makedirs(os.path.dirname(_iod_out), exist_ok=True)
    fig, ax = create_pdo_area_chart(
        pdo_df,
        highlight_points=HIGHLIGHT_POINTS,
        save_path=_iod_out
    )
