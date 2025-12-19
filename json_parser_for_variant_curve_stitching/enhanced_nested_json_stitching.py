"""
Stitch Variant Time Series JSON Files

This script combines two nested JSON files representing time series data
for SARS-CoV-2 variants (or similar) by location and variant.

It keeps:
- All entries from the old JSON **before** the earliest date in the new JSON
- All entries from the new JSON
- Any new variants or cities found only in the new JSON

USAGE:
    python stitch_variants.py --old older.json --new smoothed.json --output stitched.json

Arguments:
    --old       Path to the older JSON file (historical timepoints)
    --new       Path to the newer JSON file (smoothed or extended data)
    --output    Path to the output file that will contain the stitched result

The structure of the JSON is expected to be:
{
  "CityA": {
    "VariantX": {
      "timeseriesSummary": [
        {"date": "YYYY-MM-DD", "proportion": float, "proportionLower": float, "proportionUpper": float},
        ...
      ]
    },
    ...
  },
  ...
}
"""

import json
import logging
from typing import Dict, Any, List
import argparse
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Stitch together two nested JSON files containing time series data by location and variant."
    )
    parser.add_argument(
        "--old", required=True,
        help="Path to the older JSON file (contains earlier timepoints)."
    )
    parser.add_argument(
        "--new", required=True,
        help="Path to the newer JSON file (contains new or updated timepoints)."
    )
    parser.add_argument(
        "--output", required=True,
        help="Path to the output JSON file to write the stitched result."
    )
    return parser.parse_args()

def setup_logging() -> None:
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def load_json(filepath: str) -> Dict[str, Any]:
    """Load JSON file from disk."""
    logging.info(f"Loading JSON from: {filepath}")
    with open(filepath, "r") as f:
        return json.load(f)

def determine_stitch_date(new_data: Dict[str, Any]) -> str:
    """Determine the earliest date across all locations and variants in the new dataset."""
    all_dates = [
        entry["date"]
        for location_data in new_data.values()
        for variant_data in location_data.values()
        for entry in variant_data["timeseriesSummary"]
    ]
    stitch_date = min(all_dates)
    logging.info(f"Using stitch date: {stitch_date}")
    return stitch_date

def stitch_variant_timeseries(
    old_variant_data: Dict[str, Any],
    new_variant_data: Dict[str, Any],
    stitch_date: str,
    location: str,
    variant: str
    ) -> List[Dict[str, Any]]:
    """Combine old timepoints (before stitch date) and new timepoints (all)."""
    old_summary = old_variant_data.get("timeseriesSummary", [])
    new_summary = new_variant_data.get("timeseriesSummary", [])

    stitched_summary = [
        entry for entry in old_summary if entry["date"] < stitch_date
    ] + new_summary

    if not old_summary and new_summary:
        logging.info(f"{location} → Added **new variant**: {variant}")
    elif old_summary and new_summary:
        logging.info(f"{location} → Updated variant: {variant} (merged old+new)")
    elif old_summary and not new_summary:
        logging.info(f"{location} → Kept variant with only old data: {variant}")
    else:
        logging.warning(f"{location} → Empty data for variant: {variant}")

    return stitched_summary

def stitch_datasets(
    old_data: Dict[str, Any],
    new_data: Dict[str, Any],
    stitch_date: str
    ) -> Dict[str, Any]:
    """Stitch together two nested JSON datasets by location and variant."""
    stitched_data = {}

    # Union of locations so we also handle locations that are only in new_data
    all_locations = set(old_data.keys()) | set(new_data.keys())

    for location in all_locations:
        old_variants = old_data.get(location, {})
        new_variants = new_data.get(location, {})

        if location in old_data and location not in new_data:
            logging.info(f"{location} → Present only in OLD data; keeping pre-{stitch_date} history.")
        elif location in new_data and location not in old_data:
            logging.info(f"{location} → NEW location; taking all variants from NEW data.")

        # Union of variants to cover new/removed variants 
        all_variants = set(old_variants.keys()) | set(new_variants.keys())

        stitched_data[location] = {}
        for variant in all_variants:
            stitched_summary = stitch_variant_timeseries(
                old_variant_data=old_variants.get(variant, {}),
                new_variant_data=new_variants.get(variant, {}),
                stitch_date=stitch_date,
                location=location,
                variant=variant
            )
            stitched_data[location][variant] = {"timeseriesSummary": stitched_summary}

    return stitched_data

def save_json(data: Dict[str, Any], output_path: str):
    """Save JSON data to disk."""
    with open(output_path, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    logging.info(f"Saved stitched JSON to: {output_path}")

# --------- MAIN EXECUTION ---------

if __name__ == "__main__":
    setup_logging()  
    
    args = parse_args()

    old_data = load_json(args.old)
    new_data = load_json(args.new)
    stitch_date = determine_stitch_date(new_data)

    stitched = stitch_datasets(old_data, new_data, stitch_date)
    save_json(stitched, args.output)
