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

FUEL_MAP = {
    "Diesel Κίνησης": "diesel_driving",
    "Αμόλυβδη 100 οκτ.": "unleaded_100",
    "Αμόλυβδη 95 οκτ.": "unleaded_95",
    "Υγραέριο κίνησης (Autogas)": "autogas"
}

# -----------------------------
# Extract date from filename
# -----------------------------
def extract_date(fname):
    match = re.search(r'(\d{2})_(\d{2})_(\d{4})', fname)
    if match:
        day, month, year = match.groups()
        return pd.Timestamp(year=int(year), month=int(month), day=int(day))
    return None

# -----------------------------
# Extract data from PDF
# -----------------------------
def extract_data_from_pdf(pdf_path):
    data_dict = {}
    pdf_filename = os.path.basename(pdf_path)

    match = re.search(r'(\d{2})_(\d{2})_(\d{4})', pdf_filename)
    if match:
        day, month, year = match.groups()
        data_dict["date"] = f"{int(day)}/{int(month)}/{str(year)[-2:]}"
    else:
        return None

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        lines = page.extract_text().split("\n")

        for line in lines:
            if any(kw in line for kw in exclude_keywords):
                continue

            parts = line.split()
            if len(parts) < 2:
                continue

            price_str = parts[-1].replace(",", ".")
            try:
                price = float(price_str)
            except ValueError:
                continue

            fuel_name = " ".join(parts[:-2]) if len(parts) > 2 else parts[0]

            if fuel_name in FUEL_MAP:
                col_name = FUEL_MAP[fuel_name]
                data_dict[col_name] = price

    for col in FUEL_MAP.values():
        data_dict.setdefault(col, None)

    return pd.DataFrame([data_dict], columns=["date"] + list(FUEL_MAP.values()))

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":

    master_csv = "prices_of_petrol.csv"

    # Load CSV or create empty
    if os.path.exists(master_csv):
        master_df = pd.read_csv(master_csv)
    else:
        master_df = pd.DataFrame(columns=["date"] + list(FUEL_MAP.values()))

    # Normalize existing dates
    master_df["date"] = pd.to_datetime(master_df["date"], errors="coerce", dayfirst=True)
    master_df = master_df.dropna(subset=["date"])
    master_df["date"] = master_df["date"].dt.strftime("%d-%m-%y")

    existing_dates = set(master_df["date"].values)

    # Get all PDFs
    pdfs = [f for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf")]

    # Sort oldest → newest (important)
    pdfs.sort(key=lambda f: extract_date(f))

    new_rows = []

    for pdf_file in pdfs:
        pdf_date = extract_date(pdf_file)
        if not pdf_date:
            continue

        formatted_date = pdf_date.strftime("%d-%m-%y")

        # Skip if already exists
        if formatted_date in existing_dates:
            continue

        print(f"Processing {pdf_file}")

        pdf_path = os.path.join(PDF_FOLDER, pdf_file)
        df = extract_data_from_pdf(pdf_path)

        if df is not None:
            df["date"] = pd.to_datetime(df["date"], format="%d/%m/%y", errors="coerce")
            df["date"] = df["date"].dt.strftime("%d-%m-%y")

            new_rows.append(df)

    # Append all new rows at once
    if new_rows:
        new_data_df = pd.concat(new_rows, ignore_index=True)
        master_df = pd.concat([master_df, new_data_df], ignore_index=True)
        print(f"Added {len(new_rows)} new rows")
    else:
        print("No new data found")

    # Ensure column order
    master_df = master_df[["date", "diesel_driving", "unleaded_100", "unleaded_95", "autogas"]]
    #Sort by date
    master_df["date"] = pd.to_datetime(master_df["date"], format="%d-%m-%y", errors="coerce")
    master_df = master_df.sort_values("date").reset_index(drop=True)
    master_df["date"] = master_df["date"].dt.strftime("%d-%m-%y")

    # Save CSV
    master_df.to_csv(master_csv, index=False)

    print(f"Updated {master_csv}")