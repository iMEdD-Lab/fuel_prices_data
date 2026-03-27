#!/usr/bin/env python3

import pdfplumber
import pandas as pd
import os
import re

# -----------------------------
# Paths
# -----------------------------
PDF_FOLDER = "pdf_files"
exclude_keywords = ["Ταχ.", "Τηλέφωνο", "Fax"]

# Mapping fuel names in PDF to XLSX columns
FUEL_MAP = {
    "Diesel Κίνησης": "diesel_driving",
    "Αμόλυβδη 100 οκτ.": "unleaded_100",
    "Αμόλυβδη 95 οκτ.": "unleaded_95",
    "Υγραέριο κίνησης (Autogas)": "autogas"
}

# -----------------------------
# Get latest PDF
# -----------------------------
def get_latest_pdf(folder):
    pdfs = [f for f in os.listdir(folder) if f.endswith(".pdf")]
    if not pdfs:
        raise FileNotFoundError("No PDFs found in pdf_files folder")
    
    # Sort PDFs by date in filename: e.g., IMERISIO_DELTIO_PANELLINIO_26_03_2026.pdf
    def extract_date(fname):
        match = re.search(r'(\d{2})_(\d{2})_(\d{4})', fname)
        if match:
            day, month, year = match.groups()
            return pd.Timestamp(year=int(year), month=int(month), day=int(day))
        return pd.Timestamp.min

    pdfs.sort(key=lambda f: extract_date(f), reverse=True)
    latest_pdf = pdfs[0]
    latest_pdf_path = os.path.join(folder, latest_pdf)
    print("Latest PDF:", latest_pdf_path)
    return latest_pdf_path, extract_date(latest_pdf)

# Extract data from PDF
def extract_data_from_pdf(pdf_path):
    data_dict = {}
    pdf_filename = os.path.basename(pdf_path)
    # Extract date from filename and format as dd/mm/yy
    match = re.search(r'(\d{2})_(\d{2})_(\d{4})', pdf_filename)
    if match:
        day, month, year = match.groups()
        data_dict["date"] = f"{int(day)}/{int(month)}/{str(year)[-2:]}"
    else:
        data_dict["date"] = ""

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        lines = page.extract_text().split("\n")
        for line in lines:
            if any(kw in line for kw in exclude_keywords):
                continue
            
            parts = line.split()
            if len(parts) < 2:
                continue

            # Last part is price
            price_str = parts[-1].replace(",", ".")
            try:
                price = float(price_str)
            except ValueError:
                continue
            
            fuel_name = " ".join(parts[:-2]) if len(parts) > 2 else parts[0]
            
            # Map fuel to correct XLSX column
            if fuel_name in FUEL_MAP:
                col_name = FUEL_MAP[fuel_name]
                data_dict[col_name] = price

    # Ensure all columns exist even if missing in PDF
    for col in FUEL_MAP.values():
        data_dict.setdefault(col, None)

    # Create a single-row DataFrame with proper column order
    new_row_df = pd.DataFrame([data_dict], columns=["date"] + list(FUEL_MAP.values()))
    return new_row_df

# Main
if __name__ == "__main__":
    latest_pdf, pdf_date = get_latest_pdf(PDF_FOLDER)
    new_row_df = extract_data_from_pdf(latest_pdf)
    

# ----------------
# Merge the data with the master .xlsx
# ----------------

# Paths
master_xlsx = "/workspaces/fuel_prices/prices_of_petrol.xlsx"

# Read master XLSX
master_df = pd.read_excel(master_xlsx)

# Ensure master dates are datetime, then convert to dd-mm-yy strings
master_df["date"] = pd.to_datetime(master_df["date"], errors="coerce", dayfirst=True)
master_df = master_df.dropna(subset=["date"])
master_df["date"] = master_df["date"].dt.strftime("%d-%m-%y")

# Ensure new row date is also in dd-mm-yy string format
new_row_df["date"] = pd.to_datetime(new_row_df["date"], format="%d/%m/%y", errors="coerce")
new_row_df["date"] = new_row_df["date"].dt.strftime("%d-%m-%y")

# Check for duplicates
if new_row_df.iloc[0]["date"] in master_df["date"].values:
    print(f"Date {new_row_df.iloc[0]['date']} already exists. Skipping append.")
else:
    # Append new row at the bottom
    master_df = pd.concat([master_df, new_row_df], ignore_index=True)

# Ensure correct column order
master_df = master_df[["date", "diesel_driving", "unleaded_100", "unleaded_95", "autogas"]]

# Save back to XLSX
master_df.to_excel(master_xlsx, index=False, engine="openpyxl")

print(f"Updated {master_xlsx} with latest data.")