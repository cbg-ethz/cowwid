#!/bin/bash
set -euo pipefail

eval "$(/cluster/project/pangolin/resources/miniconda3/bin/conda shell.bash hook)"
conda activate rsv_heatmap

#current_batch="20251128_2511665243"
current_batch=$(
  find /cluster/project/pangolin/processes/rsv/RSVA/working/MutationFrequencies \
    -name '*_EPI_ISL_412866_Mutations_Dashboard.tsv' \
    -printf '%f\n' \
  | sed 's/_EPI_ISL_412866_Mutations_Dashboard.tsv$//' \
  | sort -V \
  | tail -n 1
)
echo "Processing batch:"
echo ${current_batch}
mut_file_A="/cluster/project/pangolin/processes/rsv/RSVA/working/MutationFrequencies/${current_batch}_EPI_ISL_412866_Mutations_Dashboard.tsv"
mut_file_B="/cluster/project/pangolin/processes/rsv/RSVB/working/MutationFrequencies/${current_batch}_EPI_ISL_1653999_Mutations_Dashboard.tsv"
out_path="/cluster/project/pangolin/resources/cowwid/rsv_iva_heatmaps/results_rsv"

mkdir -p ${out_path}

#RSVA
echo "Processing RSVA"
python /cluster/project/pangolin/processes/rsv/rsv_downstream_analysis/RSV-wastewater-V-pipe/regular_monitoring_2024_2025/regular_monitoring_rsva_a_annotated.py \
  --input_file ${mut_file_A} \
  --output_dir ${out_path} \
  --batch ${current_batch} \
  --subtype "RSVA"

#RSVB
echo "Processing RSVB"
python /cluster/project/pangolin/processes/rsv/rsv_downstream_analysis/RSV-wastewater-V-pipe/regular_monitoring_2024_2025/regular_monitoring_rsvb_b_annotated.py \
  --input_file ${mut_file_B} \
  --output_dir ${out_path} \
  --batch ${current_batch} \
  --subtype "RSVB"

conda deactivate