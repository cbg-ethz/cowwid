#!/bin/bash
set -euo pipefail

# === Logging ===
log_date=$(date +%Y-%m-%d_%H-%M-%S)
log_dir="/cluster/project/pangolin/resources/cowwid/covvfit/analysis/covvfit_analysis/logs"
mkdir -p "$log_dir"
log_file="$log_dir/covvfit_run_$log_date.log"

# Log function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$log_file"
}

# Trap on error
trap 'log "ERROR on line $LINENO. Exiting."' ERR
trap 'log "Script exited successfully."' EXIT

# === Start Logging ===
log "==== Starting covvfit inference run ===="

# === Environment Setup ===
log "Activating conda environment..."
eval "$(/cluster/project/pangolin/resources/miniconda3/bin/conda shell.bash hook)"
conda activate covvfit_lollipop

# === Define Paths ===
input_path="/cluster/project/pangolin/resources/cowwid/covvfit/analysis/lollipop/results"
output_path="/cluster/project/pangolin/resources/cowwid/covvfit/analysis/covvfit_analysis/results/covvfit_results_$(date +%Y-%m-%d)"
config_path="/cluster/project/pangolin/resources/cowwid/covvfit/analysis/covvfit_analysis/config"

# === Run Inference ===
# changed to half year display :--max-days 365
log "Running covvfit inference..."
covvfit infer \
    -i "$input_path/deconvolved.csv" \
    -o "$output_path" \
    -c "$config_path/covvfit_config.yaml" \
    --max-days 180 \
    --horizon 90 | tee -a "$log_file"

# === Cleanup ===
log "Deactivating conda..."
conda deactivate

log "==== covvfit inference run completed ===="
