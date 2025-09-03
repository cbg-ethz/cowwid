#!/bin/bash
#SBATCH --job-name="covvfit-LOLLIPOP"
#SBATCH --mem-per-cpu=16384
#SBATCH --oversubscribe
#SBATCH --time=5:00:00
#SBATCH --output=/cluster/project/pangolin/cowwid/covvfit/analysis/lollipop/logs/%x_%j.out   # STDOUT
#SBATCH --error=/cluster/project/pangolin/cowwid/covvfit/analysis/lollipop/logs/%x_%j.err    # STDERR


set -euo pipefail

eval "$(/cluster/project/pangolin/test_automation/miniconda3/bin/conda shell.bash hook)"

conda activate /cluster/project/pangolin/cowwid/covvfit/envs/covvfit_lollipop

ldata="/cluster/project/pangolin/work-vp-test"
config_path="/cluster/project/pangolin/cowwid/covvfit/analysis/lollipop/config"
output_path="/cluster/project/pangolin/cowwid/covvfit/analysis/lollipop/results"

zstd -d $ldata/variants/tallymut.tsv.zst 

lollipop deconvolute $ldata/variants/tallymut.tsv \
    -o $output_path/deconvolved.csv \
    --variants-config $ldata/variant_config.yaml \
    --variants-dates $ldata/var_dates.yaml \
    --deconv-config $config_path/deconv_config.yaml \
    --filters $ldata/filters_badmut.yaml  \
    --seed=42 \
    --n-cores=2

conda deactivate