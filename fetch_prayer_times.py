"""
One-time script to download a full year of prayer times from JAKIM e-Solat API.
Run this once with internet, then the kiosk works offline.

Usage: python fetch_prayer_times.py
"""

import json
import os
import sys
from datetime import datetime

import requests

import config

ESOLAT_URL = "https://www.e-solat.gov.my/index.php"


def fetch_month(year, month):
    """Fetch prayer times for a given month from e-Solat API."""
    url = "https://www.e-solat.gov.my/index.php"
    params = {
        "r": "esolatApi/takwimsolat",
        "period": "month",
        "zone": config.ZONE,
        "year": year,
        "month": month,
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    return data


def parse_prayer_data(api_data):
    """Parse e-Solat API response into our format."""
    times = {}

    if "ppiramujikirat" not in api_data and "prayerTime" not in api_data:
        return times

    prayer_list = api_data.get("prayerTime", [])

    for entry in prayer_list:
        # Date from API: "DD-Mon-YYYY" e.g. "01-Jan-2026"
        date_raw = entry.get("date", "")
        try:
            dt = datetime.strptime(date_raw.strip(), "%d-%b-%Y")
            date_key = dt.strftime("%d-%m-%Y")
        except ValueError:
            continue

        times[date_key] = {
            "hijri": entry.get("hijri", "").strip(),
            "day": entry.get("day", "").strip(),
            "subuh": entry.get("fajr", "").strip()[:5],
            "syuruk": entry.get("syuruk", "").strip()[:5],
            "zohor": entry.get("dhuhr", "").strip()[:5],
            "asar": entry.get("asr", "").strip()[:5],
            "maghrib": entry.get("maghrib", "").strip()[:5],
            "isyak": entry.get("isha", "").strip()[:5],
        }

    return times


def main():
    year = datetime.now().year
    all_times = {}

    print(f"Fetching prayer times for zone {config.ZONE}, year {year}...")

    for month in range(1, 13):
        print(f"  Fetching month {month:02d}...", end=" ")
        try:
            data = fetch_month(year, month)
            month_times = parse_prayer_data(data)
            all_times.update(month_times)
            print(f"OK ({len(month_times)} days)")
        except Exception as e:
            print(f"FAILED: {e}")

    if not all_times:
        print("ERROR: No prayer times fetched. Check API and zone code.")
        sys.exit(1)

    # Save to file
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.PRAYER_DATA_FILE, "w") as f:
        json.dump(all_times, f, indent=2)

    print(f"\nSaved {len(all_times)} days to {config.PRAYER_DATA_FILE}")


if __name__ == "__main__":
    main()
