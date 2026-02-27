#!/bin/bash
set -euo pipefail

eval "$(/cluster/project/pangolin/resources/miniconda3/bin/conda shell.bash hook)"
conda activate iva_heatmap

iva_input_path_N1="/cluster/project/pangolin/processes/influenza/IA_N1/working/mutation_frequencies/0_table_for_plotting/N1_Mutations.tsv"
iva_input_path_N2="/cluster/project/pangolin/processes/influenza/IA_N2/working/mutation_frequencies/0_table_for_plotting/N2_Mutations.tsv"
iva_input_path_H1="/cluster/project/pangolin/processes/influenza/IA_H1/working/mutation_frequencies/0_table_for_plotting/H1_Mutations.tsv"
iva_input_path_H3="/cluster/project/pangolin/processes/influenza/IA_H3/working/mutation_frequencies/0_table_for_plotting/H3_Mutations.tsv"
out_path="/cluster/project/pangolin/resources/cowwid/rsv_iva_heatmaps/results_iva"
mkdir -p $out_path

./iva_heatmapt.R \
  -i "/${iva_input_path_N1},${iva_input_path_N2},${iva_input_path_H1},${iva_input_path_H3}" \
  -o "${out_path}" \
  -r "/cluster/project/pangolin/resources/cowwid/rsv_iva_heatmaps/resources/N1_resistanceMuts.tsv"


conda deactivate