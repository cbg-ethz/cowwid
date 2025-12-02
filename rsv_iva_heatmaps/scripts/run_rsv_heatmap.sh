#!/bin/bash
set -euo pipefail

eval "$(/cluster/project/pangolin/resources/miniconda3/bin/conda shell.bash hook)"
conda activate rsv_heatmap

current_batch="20251128_2511665243"
mut_file_A="/cluster/project/pangolin/processes/rsv/RSVA/working/MutationFrequencies/${current_batch}_EPI_ISL_412866_Mutations_Dashboard.tsv"
mut_file_B="/cluster/project/pangolin/processes/rsv/RSVB/working/MutationFrequencies/${current_batch}_EPI_ISL_1653999_Mutations_Dashboard.tsv"
out_path="/cluster/project/pangolin/resources/cowwid/rsv_iva_heatmaps/results"

python rsv_heatmap.py \
  --input_file ${mut_file_A} \
  --output_dir ${out_path} \
  --batch ${current_batch} \
  --subtype "RSVA"


python rsv_heatmap.py \
  --input_file ${mut_file_A} \
  --output_dir ${out_path} \
  --batch ${current_batch} \
  --subtype "RSVB"

conda deactivate