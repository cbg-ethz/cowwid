###########################
## Name: csv_to_json.py
## Author: Matteo Carrara
## NEXUS Personalized Health Technologies
## 2025
## Description: takes in input the cov-spectrum table "wastewater_results" in csv format
##   and converts it in a json format compatible with the output from Lollipop
###########################

import csv
import json
import argparse
from collections import defaultdict
import sys

# bump the field-size limit
csv.field_size_limit(sys.maxsize)

def build_nested_dict(rows, idx2, idx1, idx3):
    # { col2_value: { col1_value: parsed_col3_obj } }
    nested = defaultdict(dict)
    for row in rows:
        k2 = row[idx2]
        k1 = row[idx1]
        # parse the JSON in col3
        try:
            v3 = json.loads(row[idx3])
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in row for {k2}/{k1}: {e}")
        nested[k2][k1] = v3
    return nested

def read_csv_no_header(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.reader(f))

def write_json(data, path):
    compact = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(compact)

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('input_csv')
    p.add_argument('output_json')
    p.add_argument('--col1_idx', type=int, default=0)
    p.add_argument('--col2_idx', type=int, default=1)
    p.add_argument('--col3_idx', type=int, default=2)
    return p.parse_args()

def main():
    args = parse_args()
    rows = read_csv_no_header(args.input_csv)
    nested = build_nested_dict(
        rows,
        idx2=args.col2_idx,
        idx1=args.col1_idx,
        idx3=args.col3_idx
    )
    write_json(nested, args.output_json)
    print(f"Written compact JSON to {args.output_json}")

if __name__=='__main__':
    main()

