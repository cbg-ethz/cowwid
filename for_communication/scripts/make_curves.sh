#!/usr/bin/env bash
set -euo pipefail

eval "$(/cluster/project/pangolin/resources/miniconda3/condabin/conda shell.bash hook)"


# TODO add here the stitching curves
echo "stitching json files (enhanced_nested_json_stitching.py)"
conda activate stitching_env

ts=$(date +"%Y-%m-%d_%H-%M-%S")

analysis_dir="/cluster/project/pangolin/resources/cowwid/json_parser_for_variant_curve_stitching"

mkdir -p "$analysis_dir/results" "$analysis_dir/logs"

# Find latest stitched output and use it as old_backup_curve
latest_stitched=$(ls -1 "$analysis_dir/results"/stitched_curve_*.json 2>/dev/null | sort | tail -n 1)

if [[ -n "$latest_stitched" ]]; then
    old_backup_curve="$latest_stitched"
    echo "Using latest stitched curve as old_backup_curve: $old_backup_curve"
else
    echo "No previous stitched curve found! Exiting"
    exit 1
fi
# the output of lollipop:
new_only_few_month_curve="/cluster/project/pangolin/processes/sars_cov_2/lollipop/variants/deconvoluted_upload.json"

python "$analysis_dir/scripts/enhanced_nested_json_stitching.py" \
  --old "$old_backup_curve" \
  --new "$new_only_few_month_curve" \
  --output "$analysis_dir/results/stitched_curve_${ts}.json" \
  > "$analysis_dir/logs/stitching_${ts}.log" 2>&1

#make a copy with fixed name to be used in config file
cp "$analysis_dir/results/stitched_curve_${ts}.json" "$analysis_dir/results/stitched_curve.json"

conda deactivate

echo "make curves (ww_cov_curves_v-pipe.py)"
conda activate communication_env

curve_analysis_dir="/cluster/project/pangolin/resources/cowwid/for_communication"
mkdir -p "$curve_analysis_dir/logs" "$curve_analysis_dir/output"

python $curve_analysis_dir/scripts/ww_cov_curves_v-pipe.py "$curve_analysis_dir/config/config.yaml" > >(tee ww_cov_curves_v-pipe.log) 2>&1
#add here the merge_json.py script -->output of this file should be uploaded to wiseDB

#'''
#def parse_args():
#    parser = argparse.ArgumentParser(
#        description="Merge two nested-JSON files into one with duplication checks.")
#    parser.add_argument('first_json', help='Path to the first input JSON file')
#    parser.add_argument('second_json', help='Path to the second input JSON file')
#    parser.add_argument('output_json', help='Path where the merged JSON will be written')
#    return parser.parse_args()
#'''

echo "merge historical data (merge_json.py)"
python $curve_analysis_dir/scripts/historical/merge_json.py \
"$curve_analysis_dir/resources/curves_untracked_wwtps.json" \
"$analysis_dir/results/stitched_curve_${ts}.json" \
"$curve_analysis_dir/output/ww_update_data_wisebd.json" \
 > "$curve_analysis_dir/logs/merge_json_${ts}.log" 2>&1

conda deactivate