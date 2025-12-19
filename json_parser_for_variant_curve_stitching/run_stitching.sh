#!/usr/bin/env bash
set -euo pipefail

source "/Users/kkirschen/mambaforge/etc/profile.d/conda.sh" 

conda activate stitching_env

ts=$(date +"%Y-%m-%d_%H-%M-%S")

python enhanced_nested_json_stitching.py --old "/Users/kkirschen/Projects/WW/24_09_2025_json_investigations/curves_untracked_wwtps.json" \
    --new "/Users/kkirschen/Projects/WW/24_09_2025_json_investigations/deconvoluted_upload.json" \
    --output "/Users/kkirschen/Projects/learnings/WW/json_parser/24_sept_2025_stitching.json" \
    > "stitching_${ts}.log" 2>&1
