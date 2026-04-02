import os
import json
import pandas as pd
import datawrapper as dw
from pathlib import Path
import math
import time

# -----------------------
# GET API KEY
# -----------------------
API_KEY = os.environ.get("DATAWRAPPER_API")
if API_KEY is None:
    raise ValueError("DATAWRAPPER_API environment variable not set!")

os.environ["DATAWRAPPER_ACCESS_TOKEN"] = API_KEY

# -----------------------
# LOAD CHART MAPPINGS
# -----------------------
CHART_CONFIG_FILE = "datawrapper_api/ids/chart_config.json"
if not Path(CHART_CONFIG_FILE).exists():
    raise FileNotFoundError(f"{CHART_CONFIG_FILE} does not exist!")

with open(CHART_CONFIG_FILE, "r", encoding="utf-8") as f:
    chart_mappings = json.load(f)

CSV_URL = "https://raw.githubusercontent.com/pmethodios/fuel_prices/main/master_pref_upd.csv"

# -----------------------
# DEFINE COLORS PER FUEL TYPE
# -----------------------
FUEL_COLORS = {
    "Αμόλυβδη 95": "#0D864A",
    "Αμόλυβδη 100": "#FFCB6F",
    "Diesel Κίνησης": "#073140",
    "Autogas": "#F54927"
}

# -----------------------
# LOAD CSV
# -----------------------
df = pd.read_csv(CSV_URL)
df['date'] = pd.to_datetime(df['date'], errors='coerce')

# Ensure numeric fuel columns
for fuel_type in FUEL_COLORS.keys():
    if fuel_type in df.columns:
        df[fuel_type] = pd.to_numeric(df[fuel_type], errors='coerce')

# -----------------------
# UPDATE EACH CHART
# -----------------------
for chart_info in chart_mappings:
    chart_id = chart_info["chart_id"]
    prefecture = chart_info["prefecture"]
    fuel_type = chart_info["fuel_type"]

    # Filter CSV for this prefecture and fuel type, from Jan 1, 2026
    df_chart = df[(df["prefecture"] == prefecture) & (df["date"] >= "2026-01-01")]
    df_chart = df_chart[["date", fuel_type]].dropna()

    # Skip if no data
    if df_chart.empty:
        print(f"No data for {prefecture} - {fuel_type}, skipping...")
        continue

    # -----------------------
    # ADD PREFECTURE AS A COLUMN
    # -----------------------
    df_chart['prefecture'] = prefecture

    # -----------------------
    # CALCULATE PER-FUEL MIN VALUE FOR Y-AXIS
    # -----------------------
    min_val = df_chart[fuel_type].min()

    # Second closest lower tenth
    lower_y = math.floor(min_val * 10) / 10 - 0.1
    lower_y = max(lower_y, 0)
    # -----------------------
    # ASSIGN COLOR
    # -----------------------
    color_category = {fuel_type: FUEL_COLORS.get(fuel_type, "#000000")}  # default black if missing

    # -----------------------
    # UPDATE CHART
    # -----------------------
    chart = dw.LineChart(
        chart_id=chart_id,
        data=df_chart,
        x_column="date",
        color_category=color_category,
        y_grid_format="0.00",
        custom_range_y=[lower_y, None],
        tooltip_x_format="DD-MM-YYYY",
        show_tooltips=True
    )

    chart.lines.clear()
    chart.lines.append(
        dw.Line(
            column=fuel_type,
            width=dw.LineWidth.MEDIUM,
            interpolation=dw.LineInterpolation.CURVED,
            show_first_value_label=True,
            show_last_value_label=True,
            show_symbols=True,
            line_symbol="circle"
        )
    )

    chart.update()
    print(f"Chart {chart_id} ({prefecture} - {fuel_type}) updated!")

    # -----------------------
    # EXPORT PNG LOCALLY
    # -----------------------
    #png_safe_pref = prefecture.replace(" ", "_").replace("ΝΟΜΟΣ_", "")
    #png_safe_fuel = fuel_type.replace(" ", "_")
    #png_filename = f"fuel_prices_{png_safe_pref}_{png_safe_fuel}.png"

    #Path("./temp_images").mkdir(parents=True, exist_ok=True)
    #local_png_path = Path("./temp_images") / png_filename
    #png_data = chart.export_png()
    #with open(local_png_path, "wb") as f:
    #    f.write(png_data)

    #print(f"PNG saved locally: {local_png_path}")
    #time.sleep(0.5)