"""
Generate a weekly digest for the Weston Wolverine Brief.

This script reads scraped crime and permit data from the `data/` directory and
renders a Markdown digest using a Jinja2 template.  A static council note can
be supplied via the environment variable `COUNCIL_NOTE`.  If not provided,
a placeholder will be used.
"""

import datetime
import os
import pathlib

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Paths
BASE_DIR = pathlib.Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
TEMPLATE_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_data():
    """Load crime and permit data from CSV files."""
    crimes_path = DATA_DIR / "crimes.csv"
    permits_path = DATA_DIR / "permit_summary.csv"

    if crimes_path.exists():
        crimes = pd.read_csv(crimes_path, parse_dates=["OCC_DATE"])
    else:
        crimes = pd.DataFrame(columns=["OCC_DATE", "OFFENCE", "MCI_CATEGORY", "NEIGHBOURHOOD_158", "DATE"])

    if permits_path.exists():
        permits = pd.read_csv(permits_path)
    else:
        permits = pd.DataFrame(columns=["WORK", "COUNT"])

    return crimes, permits


def summarise_crimes(crimes: pd.DataFrame) -> dict:
    """Return a dictionary of crime counts by category."""
    counts = crimes["MCI_CATEGORY"].value_counts().to_dict()
    return counts


def summarise_permits(permits: pd.DataFrame, top_n: int = 5) -> list:
    """Return a list of top permit types with counts."""
    if permits.empty:
        return []
    top = permits.sort_values("COUNT", ascending=False).head(top_n)
    # Convert to simple objects for Jinja2
    return [
        type("Obj", (object,), {"WORK": row["WORK"], "COUNT": int(row["COUNT"])})
        for _, row in top.iterrows()
    ]


def main():
    crimes, permits = load_data()

    # Determine week boundaries from crime dates or default to last week
    today = datetime.date.today()
    if not crimes.empty:
        start_date = crimes["DATE"].min()
        end_date = crimes["DATE"].max()
    else:
        start_date = today - datetime.timedelta(days=7)
        end_date = today

    crime_counts = summarise_crimes(crimes)
    permits_total = int(permits["COUNT"].sum()) if not permits.empty else 0
    top_permits = summarise_permits(permits)

    council_note = os.getenv(
        "COUNCIL_NOTE",
        (
            "City Council recently considered development applications at "
            "1175–1181 Weston Road and 7–17 Locust Street.  Council refused the "
            "applications and the developer has appealed to the Ontario Land Tribunal; "
            "the first case management conference is scheduled for May 20 2025."
        ),
    )

    # Set up Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(disabled_extensions=("md",))
    )
    template = env.get_template("weekly_digest.md.j2")

    content = template.render(
        start_date=start_date,
        end_date=end_date,
        total_crimes=len(crimes),
        crime_counts=crime_counts,
        permits_total=permits_total,
        top_permits=top_permits,
        council_note=council_note,
    )

    output_path = OUTPUT_DIR / "weekly_digest.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Digest generated at {output_path}")


if __name__ == "__main__":
    main()