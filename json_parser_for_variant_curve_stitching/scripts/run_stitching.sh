#!/usr/bin/env bash
set -euo pipefail

eval "$(/cluster/project/pangolin/resources/miniconda3/bin/conda shell.bash hook)"

conda activate stitching_env

ts=$(date +"%Y-%m-%d_%H-%M-%S")

analysis_dir="/cluster/project/pangolin/resources/cowwid/json_parser_for_variant_curve_stitching"
#old_backup_curve="/cluster/project/pangolin/processes/sars_cov_2/lollipop/variants/bck_20250804_deconvoluted_upload.json" #is this a valid one? otherwise get an upload from wiseDB!
#new_only_few_month_curve="/cluster/project/pangolin/processes/sars_cov_2/explore-new-variants/variants/20260119_backup_results_NO_ba32/deconvoluted_upload.json" #TBD in /cluster/project/pangolin/processes/sars_cov_2/explore-new-variants
### compare output with /cluster/project/pangolin/processes/sars_cov_2/lollipop/variants/bckup15jan_deconvoluted_upload.json

#TEST CASE
#ran lollipop on sampleset sheet with sample from different time ranges
#/cluster/project/pangolin/processes/sars_cov_2/explore-new-variants/variants/results_batch_202511
#/cluster/project/pangolin/processes/sars_cov_2/explore-new-variants/variants/results_batch_202512
#/cluster/project/pangolin/processes/sars_cov_2/explore-new-variants/variants/results_batch_202511_202512

#old_backup_curve="/cluster/project/pangolin/processes/sars_cov_2/explore-new-variants/variants/results_batch_202511/deconvoluted_upload.json"
#new_only_few_month_curve="/cluster/project/pangolin/processes/sars_cov_2/explore-new-variants/variants/results_batch_202512/deconvoluted_upload.json" 
# Test case
#old_backup_curve="/cluster/project/pangolin/processes/sars_cov_2/explore-new-variants/variants/results_batch_202511/deconvoluted_upload.json"
#new_only_few_month_curve="/cluster/project/pangolin/processes/sars_cov_2/explore-new-variants/variants/results_ba32_batch_202512/deconvoluted_upload.json"

#to create the first curve used in regular processing:
old_backup_curve="/cluster/project/pangolin/processes/sars_cov_2/lollipop/reporting_20Jan2026/deconvoluted_upload.json"
new_only_few_month_curve="/cluster/project/pangolin/processes/sars_cov_2/lollipop/variants/deconvoluted_upload.json"


python $analysis_dir/scripts/enhanced_nested_json_stitching.py \
    --old $old_backup_curve \
    --new $new_only_few_month_curve \
    --output "$analysis_dir/results/stitched_curve_${ts}.json" \
    > "$analysis_dir/logs/stitching_${ts}.log" 2>&1
