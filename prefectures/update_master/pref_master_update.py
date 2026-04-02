import re
import os
import requests
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pdfplumber
import pandas as pd

# -----------------------------
# Config
# -----------------------------
PAGE_URL = "https://www.fuelprices.gr/deltia_dn.view"
BASE_URL = "https://www.fuelprices.gr/"
DOWNLOAD_FOLDER = "pdfs_pref"
CUTOFF_DATE = datetime(2026, 3, 24)

# -----------------------------
# Extract date from filename
# -----------------------------
def extract_date(text: str):
    match = re.search(r'(\d{2})_(\d{2})_(\d{4})', text)
    if match:
        day, month, year = match.groups()
        return datetime(int(year), int(month), int(day))
    return None

# -----------------------------
# Get all relevant PDFs
# -----------------------------
def get_relevant_pdfs():
    response = requests.get(PAGE_URL)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    pdf_links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if ".pdf" not in href:
            continue

        full_url = urljoin(BASE_URL, href)
        dt = extract_date(full_url)

        # ✅ KEEP ONLY FROM CUTOFF DATE
        if dt and dt >= CUTOFF_DATE:
            pdf_links.append((full_url, dt))

    if not pdf_links:
        raise Exception("No PDFs found after cutoff date")

    # Sort newest → oldest
    pdf_links.sort(key=lambda x: x[1], reverse=True)

    print(f"\nFound {len(pdf_links)} PDFs after {CUTOFF_DATE.strftime('%d/%m/%Y')}")
    return pdf_links

# -----------------------------
# Download missing PDFs
# -----------------------------
def download_missing_pdfs():
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

    existing_files = set(os.listdir(DOWNLOAD_FOLDER))

    pdfs = get_relevant_pdfs()

    new_downloads = 0

    for url, dt in pdfs:
        filename = url.split("/")[-1]

        # ✅ Skip if already exists
        if filename in existing_files:
            continue

        print(f"Downloading {filename}...")
        response = requests.get(url)
        response.raise_for_status()

        filepath = os.path.join(DOWNLOAD_FOLDER, filename)

        with open(filepath, "wb") as f:
            f.write(response.content)

        print(f"Saved: {filepath}")
        new_downloads += 1

    if new_downloads == 0:
        print("\nNo new PDFs to download.")
    else:
        print(f"\nDownloaded {new_downloads} new PDFs.")

# -----------------------------
# Create dataframe
# -----------------------------
MASTER_COLUMNS = [
    "date",
    "prefecture",
    "Αμόλυβδη 95",
    "Αμόλυβδη 100",
    "Diesel Κίνησης",
    "Autogas",
    "Diesel Θέρμανσης",
    "Super"
]

def build_prefecture_df_for_master():
    folder = "pdfs_pref"
    all_data = []

    # Original PDF column names
    FUEL_COLUMNS = [
        "unleaded_95",
        "unleaded_100",
        "diesel_driving",
        "autogas",
        "diesel_heating"
    ]

    for file in os.listdir(folder):
        if not file.endswith(".pdf"):
            continue

        path = os.path.join(folder, file)

        # Extract date from filename
        match = re.search(r'(\d{2})_(\d{2})_(\d{4})', file)
        if match:
            day, month, year = match.groups()
            date = f"{int(day)}/{int(month)}/{str(year)[-2:]}"
        else:
            date = ""

        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                lines = page.extract_text().split("\n")

                for line in lines:
                    if not line.startswith("ΝΟΜΟΣ"):
                        continue

                    parts = line.split()
                    if len(parts) < 6:
                        continue

                    prefecture = " ".join(parts[:-5])
                    numeric_parts = parts[-5:]

                    prices = []
                    for p in numeric_parts:
                        try:
                            val = float(p.replace(",", "."))
                            prices.append(val)
                        except ValueError:
                            prices.append(None)

                    # Pad prices if missing (e.g., heating diesel missing)
                    while len(prices) < len(FUEL_COLUMNS):
                        prices.append(None)

                    row = {"date": date, "prefecture": prefecture}
                    for i, col in enumerate(FUEL_COLUMNS):
                        row[col] = prices[i]

                    all_data.append(row)

    df = pd.DataFrame(all_data)

    # --- Rename columns to match master ---
    rename_map = {
        "unleaded_95": "Αμόλυβδη 95",
        "unleaded_100": "Αμόλυβδη 100",
        "diesel_driving": "Diesel Κίνησης",
        "autogas": "Autogas",
        "diesel_heating": "Diesel Θέρμανσης"
    }
    df = df.rename(columns=rename_map)

    # Ensure all columns exist
    for col in MASTER_COLUMNS:
        if col not in df.columns:
            df[col] = None

    # Reorder columns to match master
    df = df[MASTER_COLUMNS]

    return df

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    download_missing_pdfs()

    df = build_prefecture_df_for_master()

    print(f"Total rows: {len(df)}")

    master_df = pd.read_csv("fuel_prices/prefectures/update_master/master_pref_old.csv", index_col=False)

    # Strip whitespace from column names
    master_df.columns = master_df.columns.str.strip()

    # Parse old CSV dates explicitly: YYYY-MM-DD
    master_df['date'] = pd.to_datetime(master_df['date'], format="%Y-%m-%d", errors='coerce')

    # --- New PDF-derived df ---
    # Dates from PDF are in D/M/YY format, e.g., 26/3/26
    df['date'] = pd.to_datetime(df['date'], format="%d/%m/%y", errors='coerce')    # Drop wrong column in old df
   
    # Delete first column of old df
    if "Unnamed: 0" in master_df.columns:
        master_df = master_df.drop(columns=["Unnamed: 0"])


    # Ensure numeric columns are floats
    #NUMERIC_COLS = ["Αμόλυβδη 95", "Αμόλυβδη 100", "Diesel Κίνησης", "Autogas", "Diesel Θέρμανσης", "Super"]
    #for col in NUMERIC_COLS:
    #    master_df[col] = pd.to_numeric(master_df[col], errors='coerce')
    #    df[col] = pd.to_numeric(df[col], errors='coerce')
    # Concatenate
    combined_df = pd.concat([master_df, df], ignore_index=True)

    # Remove duplicates, keep last
    combined_df = combined_df.drop_duplicates(subset=['date', 'prefecture'], keep='last')

    # Sort by date ascending
    combined_df = combined_df.sort_values(['date', 'prefecture'], ascending=[True, True]).reset_index(drop=True)

    # Save CSV
    combined_df.to_csv("master_pref_upd.csv", index=False, date_format="%Y-%m-%d")    