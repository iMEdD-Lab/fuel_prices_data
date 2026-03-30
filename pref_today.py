import re
import os
import requests
import pdfplumber
import pandas as pd
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# -----------------------------
# Config
# -----------------------------
PAGE_URL = "https://www.fuelprices.gr/deltia_dn.view"
BASE_URL = "https://www.fuelprices.gr/"
DOWNLOAD_FOLDER = "pdfs_pref"
CUTOFF_DATE = datetime(2026, 3, 26)

FUEL_COLUMNS = [
    "unleaded_95",
    "unleaded_100",
    "diesel_driving",
    "autogas"
    ]

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
# Get relevant PDFs
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

        if dt and dt >= CUTOFF_DATE:
            pdf_links.append((full_url, dt))

    if not pdf_links:
        raise Exception("No PDFs found after cutoff date")

    pdf_links.sort(key=lambda x: x[1], reverse=True)
    return pdf_links

# -----------------------------
# Download missing PDFs
# -----------------------------
def download_missing_pdfs():
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    existing_files = set(os.listdir(DOWNLOAD_FOLDER))

    pdfs = get_relevant_pdfs()

    for url, dt in pdfs:
        filename = url.split("/")[-1]

        if filename in existing_files:
            continue

        print(f"Downloading {filename}...")
        response = requests.get(url)
        response.raise_for_status()

        with open(os.path.join(DOWNLOAD_FOLDER, filename), "wb") as f:
            f.write(response.content)

# -----------------------------
# Get latest PDF locally
# -----------------------------
def get_latest_local_pdf():
    pdfs = [f for f in os.listdir(DOWNLOAD_FOLDER) if f.endswith(".pdf")]
    if not pdfs:
        raise Exception("No local PDFs found")

    pdfs.sort(key=lambda f: extract_date(f), reverse=True)
    latest_file = pdfs[0]
    return os.path.join(DOWNLOAD_FOLDER, latest_file), extract_date(latest_file)

# -----------------------------
# Extract table from PDF
# -----------------------------

def extract_table(pdf_path):
    rows = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:  # 🔥 loop through ALL pages
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")

            for line in lines:
                # Keep only table rows
                if not line.startswith("ΝΟΜΟΣ"):
                    continue

                # Skip header row
                if "Αμόλυβδη" in line:
                    continue

                parts = line.split()

                # Must contain prefecture + 5 prices
                if len(parts) < 6:
                    continue

                # Last 5 values = prices
                price_parts = parts[-5:]
                name_parts = parts[:-5]

                prefecture = " ".join(name_parts).strip()

                prices = []
                valid_row = True

                for p in price_parts:
                    try:
                        prices.append(float(p.replace(",", ".")))
                    except ValueError:
                        valid_row = False
                        break

                if not valid_row:
                    continue

                row = {"prefecture": prefecture}
                for i, col in enumerate(FUEL_COLUMNS):
                    row[col] = prices[i]

                rows.append(row)

    df = pd.DataFrame(rows)

    return df
# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    # Step 1: Download missing PDFs
    download_missing_pdfs()

    # Step 2: Get latest PDF
    latest_pdf, latest_date = get_latest_local_pdf()
    print("Latest PDF:", latest_pdf)

    # Step 3: Extract table
    df_latest = extract_table(latest_pdf)

    # Step 4: Add date column
    df_latest.insert(0, "date", latest_date.strftime("%d-%m-%Y"))

    PREF_MAP = {
    "ΝΟΜΟΣ ΑΤΤΙΚΗΣ": "ATHINON",
    "ΝΟΜΟΣ ΑΙΤΩΛΙΑΣ ΚΑΙ ΑΚΑΡΝΑΝΙΑΣ": "ETOLOAKARNANIAS",
    "ΝΟΜΟΣ ΑΡΓΟΛΙΔΟΣ": "ARGOLIDAS",
    "ΝΟΜΟΣ ΑΡΚΑΔΙΑΣ": "ARKADIAS",
    "ΝΟΜΟΣ ΑΡΤΗΣ": "ARTAS",
    "ΝΟΜΟΣ ΑΧΑΪΑΣ": "ACHAIAS",
    "ΝΟΜΟΣ ΒΟΙΩΤΙΑΣ": "VIOTIAS",
    "ΝΟΜΟΣ ΓΡΕΒΕΝΩΝ": "GREVENON",
    "ΝΟΜΟΣ ΔΡΑΜΑΣ": "DRAMAS",
    "ΝΟΜΟΣ ΔΩΔΕΚΑΝΗΣΟΥ": "DODEKANISON",
    "ΝΟΜΟΣ ΕΒΡΟΥ": "EVROU",
    "ΝΟΜΟΣ ΕΥΒΟΙΑΣ": "EVVIAS",
    "ΝΟΜΟΣ ΕΥΡΥΤΑΝΙΑΣ": "EVRYTANIAS",
    "ΝΟΜΟΣ ΖΑΚΥΝΘΟΥ": "ZAKYNTHOU",
    "ΝΟΜΟΣ ΗΛΕΙΑΣ": "ILIAS",
    "ΝΟΜΟΣ ΗΜΑΘΙΑΣ": "IMATHIAS",
    "ΝΟΜΟΣ ΗΡΑΚΛΕΙΟΥ": "IRAKLIOU",
    "ΝΟΜΟΣ ΘΕΣΠΡΩΤΙΑΣ": "THESPROTIAS",
    "ΝΟΜΟΣ ΘΕΣΣΑΛΟΝΙΚΗΣ": "THESSALONIKIS",
    "ΝΟΜΟΣ ΙΩΑΝΝΙΝΩΝ": "IOANNINON",
    "ΝΟΜΟΣ ΚΑΒΑΛΑΣ": "KAVALAS",
    "ΝΟΜΟΣ ΚΑΡΔΙΤΣΗΣ": "KARDITSAS",
    "ΝΟΜΟΣ ΚΑΣΤΟΡΙΑΣ": "KASTORIAS",
    "ΝΟΜΟΣ ΚΕΡΚΥΡΑΣ": "KERKYRAS",
    "ΝΟΜΟΣ ΚΕΦΑΛΛΗΝΙΑΣ": "KEFALLONIAS",
    "ΝΟΜΟΣ ΚΙΛΚΙΣ": "KILKIS",
    "ΝΟΜΟΣ ΚΟΖΑΝΗΣ": "KOZANIS",
    "ΝΟΜΟΣ ΚΟΡΙΝΘΙΑΣ": "KORINTHOU",
    "ΝΟΜΟΣ ΚΥΚΛΑΔΩΝ": "KYKLADON",
    "ΝΟΜΟΣ ΛΑΚΩΝΙΑΣ": "LAKONIAS",
    "ΝΟΜΟΣ ΛΑΡΙΣΗΣ": "LARISAS",
    "ΝΟΜΟΣ ΛΑΣΙΘΙΟΥ": "LASITHIOU",
    "ΝΟΜΟΣ ΛΕΣΒΟΥ": "LESVOU",
    "ΝΟΜΟΣ ΛΕΥΚΑΔΟΣ": "LEFKADAS",
    "ΝΟΜΟΣ ΜΑΓΝΗΣΙΑΣ": "MAGNISIAS",
    "ΝΟΜΟΣ ΜΕΣΣΗΝΙΑΣ": "MESSINIAS",
    "ΝΟΜΟΣ ΞΑΝΘΗΣ": "XANTHIS",
    "ΝΟΜΟΣ ΠΕΛΛΗΣ": "PELLAS",
    "ΝΟΜΟΣ ΠΙΕΡΙΑΣ": "PIERIAS",
    "ΝΟΜΟΣ ΠΡΕΒΕΖΗΣ": "PREVEZAS",
    "ΝΟΜΟΣ ΡΕΘΥΜΝΗΣ": "RETHYMNOU",
    "ΝΟΜΟΣ ΡΟΔΟΠΗΣ": "RODOPIS",
    "ΝΟΜΟΣ ΣΑΜΟΥ": "SAMOU",
    "ΝΟΜΟΣ ΣΕΡΡΩΝ": "SERRON",
    "ΝΟΜΟΣ ΤΡΙΚΑΛΩΝ": "TRIKALON",
    "ΝΟΜΟΣ ΦΘΙΩΤΙΔΟΣ": "FTHIOTIDAS",
    "ΝΟΜΟΣ ΦΛΩΡΙΝΗΣ": "FLORINAS",
    "ΝΟΜΟΣ ΦΩΚΙΔΟΣ": "FOKIDAS",
    "ΝΟΜΟΣ ΧΑΛΚΙΔΙΚΗΣ": "CHALKIDIKIS",
    "ΝΟΜΟΣ ΧΑΝΙΩΝ": "CHANION",
    "ΝΟΜΟΣ ΧΙΟΥ": "CHIOU"
    }
    df_latest["prefecture_eng"] = df_latest["prefecture"].map(PREF_MAP)

    # -----------------------------
    # Expand ATTICA into 4 regions
    # -----------------------------
    attica_mask = df_latest["prefecture"] == "ΝΟΜΟΣ ΑΤΤΙΚΗΣ"

    attica_rows = df_latest[attica_mask]

    # Create 4 duplicates with different region names
    attica_expanded = pd.concat([
        attica_rows.assign(prefecture_eng="ATHINON"),
        attica_rows.assign(prefecture_eng="ANATOLIKIS ATTIKIS"),
        attica_rows.assign(prefecture_eng="DYTIKIS ATTIKIS"),
        attica_rows.assign(prefecture_eng="PIREOS KE NISON"),
    ])

    # Remove original ATTICA row
    df_latest = df_latest[~attica_mask]

    # Add expanded rows
    df_latest = pd.concat([df_latest, attica_expanded], ignore_index=True)

    # Final result
    print(df_latest)
    print(f"\nRows: {len(df_latest)}")

    #Save as csv
    df_latest.to_csv("pref_latest.csv")