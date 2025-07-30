"""
Scraper for the Weston Wolverine Brief.

This module fetches data from public sources:

* Toronto Police Major Crime Indicators (ArcGIS feature service) – filtered for
  the Weston neighbourhoods.
* City of Toronto Active Building Permits (CSV) – filtered for postal prefixes
  beginning with `M9N`.

The script writes raw JSON/CSV files into a `data/` directory for later use by
the digest generator.

Run with `python scraper.py`.  Adjust the start date via the `DAYS_BACK`
environment variable if desired.
"""

import datetime
import json
import os
import pathlib
from typing import List

from dotenv import load_dotenv

import pandas as pd
import requests

# Constants for external endpoints
MCI_ENDPOINT = (
    "https://services.arcgis.com/S9th0jAJ7bqgIRjw/ArcGIS/rest/services/"
    "Major_Crime_Indicators_Open_Data/FeatureServer/0/query"
)

PERMITS_CSV_URL = (
    "https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/108c2bd1-6945-46f6-"
    "af92-02f5658ee7f7/resource/dfce3b7b-4f17-4a9d-9155-5e390a5ffa97/download/"
    "building-permits-active-permits.csv"
)

# Directory for downloaded data
DATA_DIR = pathlib.Path(__file__).parent / "data"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)


def fetch_crime_data(
    start_date: datetime.date,
    neighbourhoods: List[str] = None,
    max_records: int = 10000,
) -> pd.DataFrame:
    """Fetch crime occurrences from the ArcGIS service.

    Parameters
    ----------
    start_date : datetime.date
        Only records on or after this date are returned.
    neighbourhoods : List[str]
        List of neighbourhood names to include.  Defaults to Weston and Weston‑Pelham Park.
    max_records : int
        Safety cap on the total number of records returned across all pages.

    Returns
    -------
    pandas.DataFrame
        DataFrame with columns OCC_DATE, OFFENCE, MCI_CATEGORY, NEIGHBOURHOOD_158
    """
    if neighbourhoods is None:
        neighbourhoods = ["Weston (113)", "Weston-Pelham Park (91)"]

    # Build the WHERE clause
    date_str = start_date.isoformat()
    neigh_clauses = [f"NEIGHBOURHOOD_158 = '{n}'" for n in neighbourhoods]
    where = f"({' OR '.join(neigh_clauses)}) AND OCC_DATE >= DATE '{date_str}'"

    # ArcGIS returns 2000 records per page by default; we'll paginate
    records: List[dict] = []
    offset = 0
    per_page = 2000

    while True:
        params = {
            "where": where,
            "outFields": "OCC_DATE,OFFENCE,MCI_CATEGORY,NEIGHBOURHOOD_158",
            "returnGeometry": "false",
            "orderByFields": "OCC_DATE DESC",
            "f": "json",
            "resultOffset": offset,
            "resultRecordCount": per_page,
        }
        response = requests.get(MCI_ENDPOINT, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        feats = data.get("features", [])
        if not feats:
            break
        for feat in feats:
            records.append(feat["attributes"])
            if len(records) >= max_records:
                break
        if len(feats) < per_page or len(records) >= max_records:
            break
        offset += per_page

    # Convert to DataFrame
    df = pd.DataFrame(records)
    if not df.empty:
        df["OCC_DATE"] = pd.to_datetime(df["OCC_DATE"], unit="ms", utc=True)
        df["DATE"] = df["OCC_DATE"].dt.tz_convert("America/Toronto").dt.date
    return df


def fetch_permit_summary(postal_prefix: str = "M9N", rows: int = 50000) -> pd.DataFrame:
    """Download a subset of the building permits CSV and compute summary by work type.

    Parameters
    ----------
    postal_prefix : str
        Postal code prefix to filter (e.g., 'M9N').
    rows : int
        Number of rows to read from the CSV.  The dataset is large (~87 MB);
        reading the entire file can be memory‑intensive.  Adjust as needed.

    Returns
    -------
    pandas.DataFrame
        A DataFrame with columns WORK and COUNT summarising active permits.
    """
    # Stream first `rows` lines to avoid memory blowup
    df = pd.read_csv(PERMITS_CSV_URL, nrows=rows, low_memory=False)
    df = df[df["POSTAL"].astype(str).str.startswith(postal_prefix)]
    summary = df["WORK"].value_counts().rename_axis("WORK").reset_index(name="COUNT")
    return summary


def save_dataframe(df: pd.DataFrame, filename: str) -> None:
    """Save DataFrame as CSV under the data directory."""
    filepath = DATA_DIR / filename
    df.to_csv(filepath, index=False)


def main() -> None:
    load_dotenv()
    # Determine start date from environment or default to 7 days ago
    days_back = int(os.environ.get("DAYS_BACK", 7))
    start_date = datetime.date.today() - datetime.timedelta(days=days_back)
    print(f"Fetching crime data since {start_date}…")
    crimes = fetch_crime_data(start_date)
    if crimes.empty:
        print("No crime data found for the selected period.")
    else:
        print(f"Fetched {len(crimes)} crime records.")
        save_dataframe(crimes, "crimes.csv")

    print("Fetching permit summary…")
    permits_summary = fetch_permit_summary()
    save_dataframe(permits_summary, "permit_summary.csv")
    print("Saved permit summary.")


if __name__ == "__main__":
    main()
