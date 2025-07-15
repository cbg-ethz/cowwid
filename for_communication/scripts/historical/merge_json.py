###########################
## Name: merge_json.py
## Author: Matteo Carrara
## NEXUS Personalized Health Technologies
## 2025
## Description: takes in input two lollipop-compatible json files and merge them.
##   The script checks for duplicates and throws an error if multiple time series for
##   the same virus in the same location are present
###########################

import json
import argparse
import sys


def load_json(path):
    """
    Load JSON data from the given file path.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading JSON from {path}: {e}", file=sys.stderr)
        sys.exit(1)


def write_json(data, path):
    """
    Write data as compact JSON to the given file path.
    """
    try:
        compact = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(compact)
    except Exception as e:
        print(f"Error writing JSON to {path}: {e}", file=sys.stderr)
        sys.exit(1)


def recursive_merge(a, b):
    """
    Recursively merge b into a:
      - dicts: merge keys; if both values are dict/list, merge; else b overrides.
      - lists: concatenate.
      - other: b overrides.
    """
    if isinstance(a, dict) and isinstance(b, dict):
        result = dict(a)
        for key, b_val in b.items():
            if key in result:
                result[key] = recursive_merge(result[key], b_val)
            else:
                result[key] = b_val
        return result
    if isinstance(a, list) and isinstance(b, list):
        return a + b
    return b


def parse_args():
    parser = argparse.ArgumentParser(
        description="Merge two nested-JSON files into one with duplication checks.")
    parser.add_argument('first_json', help='Path to the first input JSON file')
    parser.add_argument('second_json', help='Path to the second input JSON file')
    parser.add_argument('output_json', help='Path where the merged JSON will be written')
    return parser.parse_args()


def main():
    args = parse_args()
    json1 = load_json(args.first_json)
    json2 = load_json(args.second_json)

    # Check for duplicates at the first two nesting levels
    duplicates = []
    for top_key, subdict in json2.items():
        if isinstance(subdict, dict) and top_key in json1 and isinstance(json1[top_key], dict):
            for sub_key in subdict:
                if sub_key in json1[top_key]:
                    duplicates.append(f"{top_key}/{sub_key}")

    if duplicates:
        print(
            "Error: Duplicate entries found at the first two nesting levels:",
            ", ".join(duplicates),
            file=sys.stderr
        )
        sys.exit(1)

    merged = recursive_merge(json1, json2)
    write_json(merged, args.output_json)
    print(f"Merged JSON written to '{args.output_json}'")


if __name__ == '__main__':
    main()

