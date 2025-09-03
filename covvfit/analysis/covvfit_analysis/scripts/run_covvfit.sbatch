#!/bin/bash
#SBATCH --job-name="covvfit"
#SBATCH --mem-per-cpu=16384
#SBATCH --oversubscribe
#SBATCH --time=24:00:00
#SBATCH --output=/cluster/project/pangolin/cowwid/covvfit/analysis/covvfit_analysis/logs/%x_%j.out   # STDOUT
#SBATCH --error=/cluster/project/pangolin/cowwid/covvfit/analysis/covvfit_analysis/logs/%x_%j.err    # STDERR

set -euo pipefail

eval "$(/cluster/project/pangolin/test_automation/miniconda3/bin/conda shell.bash hook)"

conda activate /cluster/project/pangolin/cowwid/covvfit/envs/covvfit_lollipop

input_path="/cluster/project/pangolin/cowwid/covvfit/analysis/lollipop/results"
output_path="/cluster/project/pangolin/cowwid/covvfit/analysis/covvfit_analysis/results/covvfit_results"
config_path="/cluster/project/pangolin/cowwid/covvfit/analysis/covvfit_analysis/config"

covvfit infer \
    -i $input_path/deconvolved.csv \
    -o $output_path \
    -c $config_path/covvfit_config.yaml \
    --max-days 365 \
    --horizon 90

conda deactivate