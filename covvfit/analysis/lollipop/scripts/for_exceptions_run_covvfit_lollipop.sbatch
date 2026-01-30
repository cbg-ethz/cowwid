#!/bin/bash
#SBATCH --job-name="covvfit-LOLLIPOP"
#SBATCH --mem-per-cpu=16384
#SBATCH --oversubscribe
#SBATCH --time=0:30:00
#SBATCH --output=/cluster/project/pangolin/resources/cowwid/covvfit/analysis/lollipop/logs/%x_%j.out   # STDOUT
#SBATCH --error=/cluster/project/pangolin/resources/cowwid/covvfit/analysis/lollipop/logs/%x_%j.err    # STDERR


set -euo pipefail

eval "$(/cluster/project/pangolin/resources/miniconda3/bin/conda shell.bash hook)"

conda activate covvfit_lollipop

#ldata="/cluster/project/pangolin/processes/sars_cov_2/lollipop"
# saved the relevant backup files in the following folder
ldata="/cluster/project/pangolin/processes/sars_cov_2/lollipop/reporting_20Jan2026"
config_path="/cluster/project/pangolin/resources/cowwid/covvfit/analysis/lollipop/config"
output_path="/cluster/project/pangolin/resources/cowwid/covvfit/analysis/lollipop/20260119_results"

#zstd -d -f $ldata/tallymut.tsv.zst 
mkdir -p $output_path

lollipop deconvolute $ldata/tallymut.tsv \
    -o $output_path/deconvolved.csv \
    --variants-config $ldata/variant_config.yaml \
    --variants-dates $ldata/var_dates.yaml \
    --deconv-config $config_path/deconv_config.yaml \
    --filters $ldata/filters_badmut.yaml  \
    --seed=42 \
    --n-cores=2

conda deactivate
