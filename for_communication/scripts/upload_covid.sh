#!/bin/bash
set -euo pipefail

eval "$(/cluster/project/pangolin/resources/miniconda3/bin/conda shell.bash hook)"

conda activate communication_env

python /cluster/project/pangolin/resources/cowwid/for_communication/scripts/ww_cov_uploader_v-pipe.py "/cluster/project/pangolin/resources/cowwid/for_communication/config/config.yaml" > >(tee ww_cov_uploader_v-pipe.log) 2>&1

conda deactivate