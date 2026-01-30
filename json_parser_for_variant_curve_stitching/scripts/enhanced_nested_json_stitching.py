"""
Stitch Variant Time Series JSON Files

This script combines two nested JSON files representing time series data
for SARS-CoV-2 variants (or similar) by location and variant.

It keeps:
- All entries from the old JSON **before** the earliest date in the new JSON (per location)
- All entries from the new JSON
- Any new variants or cities found only in the new JSON

Additionally:
- Within each location, every variant will have a timeseriesSummary covering the same set of dates
  (a shared date grid). Missing dates are filled with zeros:
    proportion=0, proportionLower=0, proportionUpper=0

USAGE:
    python stitch_variants.py --old older.json --new smoothed.json --output stitched.json
"""

import json
import logging
from typing import Dict, Any, List, Set
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)

ZERO_ROW = {"proportion": 0.0, "proportionLower": 0.0, "proportionUpper": 0.0}

def parse_args():
    parser = argparse.ArgumentParser(
        description="Stitch together two nested JSON files containing time series data by location and variant."
    )
    parser.add_argument("--old", required=True, help="Path to the older JSON file (contains earlier timepoints).")
    parser.add_argument("--new", required=True, help="Path to the newer JSON file (contains new or updated timepoints).")
    parser.add_argument("--output", required=True, help="Path to the output JSON file to write the stitched result.")
    return parser.parse_args()

def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def load_json(filepath: str) -> Dict[str, Any]:
    logging.info(f"Loading JSON from: {filepath}")
    with open(filepath, "r") as f:
        return json.load(f)

def save_json(data: Dict[str, Any], output_path: str):
    with open(output_path, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    logging.info(f"Saved stitched JSON to: {output_path}")

def determine_stitch_dates_per_location(new_data: Dict[str, Any]) -> Dict[str, str]:
    """Earliest date in NEW data for each location."""
    stitch_dates: Dict[str, str] = {}
    for location, location_data in new_data.items():
        dates = [
            entry["date"]
            for variant_data in location_data.values()
            for entry in variant_data.get("timeseriesSummary", [])
            if isinstance(entry, dict) and "date" in entry
        ]
        if dates:
            stitch_dates[location] = min(dates)
            logging.info(f"{location} → stitch date: {stitch_dates[location]}")
        else:
            logging.warning(f"{location} → no dates in NEW data; no stitch date computed.")
    return stitch_dates

def index_by_date(ts: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Map date -> row. Assumes dates should be unique (last wins if not).
    Convert a timeseriesSummary list into a dict keyed by date.

    Why this is needed:
    - Lists have no semantic key; index order is not meaningful for time series
    - Enables merging OLD and NEW data by date (NEW overwrites OLD on overlap)
    - Enforces one entry per date (dates are the primary key)
    - Allows reliable filling of missing dates when building a shared date grid

    Without this, stitching and alignment would be order-dependent and incorrect.
    """
    out: Dict[str, Dict[str, Any]] = {}
    for row in ts or []:
        if isinstance(row, dict) and row.get("date"):
            out[row["date"]] = row
    return out

def collect_location_date_grid(old_variants: Dict[str, Any], new_variants: Dict[str, Any]) -> List[str]:
    """Union of all dates across OLD+NEW for a location (shared date grid)."""
    dates: Set[str] = set()
    for variants in (old_variants, new_variants):
        for vdata in (variants or {}).values():
            for row in (vdata or {}).get("timeseriesSummary", []):
                if isinstance(row, dict) and row.get("date"):
                    dates.add(row["date"])
    return sorted(dates)

def stitch_variant_timeseries(
    old_variant_data: Dict[str, Any],
    new_variant_data: Dict[str, Any],
    stitch_date: str,
    location: str,
    variant: str
) -> Dict[str, Dict[str, Any]]:
    """
    Merge by date with:
      - Keep OLD entries with date < stitch_date
      - Take ALL NEW entries
      - If same date exists in both, NEW wins
    Returns date->row (not yet grid-filled).
    """
    old_summary = old_variant_data.get("timeseriesSummary", [])
    new_summary = new_variant_data.get("timeseriesSummary", [])

    old_kept = [e for e in old_summary if isinstance(e, dict) and e.get("date") and e["date"] < stitch_date]
    old_by_date = index_by_date(old_kept)
    new_by_date = index_by_date(new_summary)

    merged = dict(old_by_date)
    merged.update(new_by_date)  # prefer NEW on overlap

    if not old_summary and new_summary:
        logging.info(f"{location} → Added new variant: {variant}")
    elif old_summary and new_summary:
        logging.info(f"{location} → Updated variant: {variant} (merged old+new)")
    elif old_summary and not new_summary:
        logging.info(f"{location} → Kept variant with only old data: {variant}")
    else:
        logging.warning(f"{location} → Empty data for variant: {variant}")

    return merged

def fill_variant_to_grid(merged_by_date: Dict[str, Dict[str, Any]], grid_dates: List[str]) -> List[Dict[str, Any]]:
    """Ensure variant has an entry for every date in the grid; fill missing with zeros."""
    out: List[Dict[str, Any]] = []
    for d in grid_dates:
        row = merged_by_date.get(d)
        if row is None:
            row = {"date": d, **ZERO_ROW}
        out.append(row)
    return out

def stitch_datasets(
    old_data: Dict[str, Any],
    new_data: Dict[str, Any],
    stitch_dates: Dict[str, str]
) -> Dict[str, Any]:
    stitched_data: Dict[str, Any] = {}
    all_locations = set(old_data.keys()) | set(new_data.keys())

    for location in all_locations:
        old_variants = old_data.get(location, {}) or {}
        new_variants = new_data.get(location, {}) or {}

        location_stitch_date = stitch_dates.get(location)

        # Location absent in NEW: keep OLD, but still enforce shared grid within location (from OLD)
        if location_stitch_date is None and location in old_data and location not in new_data:
            logging.info(f"{location} → Present only in OLD data; keeping all OLD history (no stitch date).")
            grid = collect_location_date_grid(old_variants, {})
            stitched_data[location] = {}
            for variant, vdata in old_variants.items():
                merged_by_date = index_by_date((vdata or {}).get("timeseriesSummary", []))
                stitched_data[location][variant] = {"timeseriesSummary": fill_variant_to_grid(merged_by_date, grid)}
            continue

        # Location only in NEW: take NEW, but enforce shared grid within location (from NEW)
        if location_stitch_date is None and location in new_data and location not in old_data:
            logging.info(f"{location} → NEW location; taking all variants from NEW data (no stitch date).")
            grid = collect_location_date_grid({}, new_variants)
            stitched_data[location] = {}
            for variant, vdata in new_variants.items():
                merged_by_date = index_by_date((vdata or {}).get("timeseriesSummary", []))
                stitched_data[location][variant] = {"timeseriesSummary": fill_variant_to_grid(merged_by_date, grid)}
            continue

        # If present in both but NEW has no dates, fall back to concatenation without filtering
        if location_stitch_date is None:
            logging.warning(f"{location} → No stitch date; concatenating old+new without filtering.")
            location_stitch_date = "0000-00-00"

        # Shared date grid = union across OLD+NEW for this location
        grid = collect_location_date_grid(old_variants, new_variants)

        all_variants = set(old_variants.keys()) | set(new_variants.keys())
        stitched_data[location] = {}

        for variant in all_variants:
            merged_by_date = stitch_variant_timeseries(
                old_variant_data=old_variants.get(variant, {}) or {},
                new_variant_data=new_variants.get(variant, {}) or {},
                stitch_date=location_stitch_date,
                location=location,
                variant=variant
            )
            stitched_ts = fill_variant_to_grid(merged_by_date, grid)
            stitched_data[location][variant] = {"timeseriesSummary": stitched_ts}

    return stitched_data

# --------- MAIN EXECUTION ---------

if __name__ == "__main__":
    setup_logging()
    args = parse_args()

    old_data = load_json(args.old)
    new_data = load_json(args.new)
    stitch_dates = determine_stitch_dates_per_location(new_data)

    stitched = stitch_datasets(old_data, new_data, stitch_dates)
    save_json(stitched, args.output)