#!/usr/bin/env python3

import re
import os
import requests
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# -----------------------------
# Config
# -----------------------------
PAGE_URL = "https://www.fuelprices.gr/deltia_d.view"
BASE_URL = "https://www.fuelprices.gr/"
DOWNLOAD_FOLDER = "pdf_files"
CUTOFF_DATE = datetime(2026, 3, 26)

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
# Main
# -----------------------------
if __name__ == "__main__":
    download_missing_pdfs()