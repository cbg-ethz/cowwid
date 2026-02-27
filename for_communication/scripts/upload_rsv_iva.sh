#!/bin/bash
set -euo pipefail

eval "$(/cluster/project/pangolin/resources/miniconda3/bin/conda shell.bash hook)"

conda activate communication_env

#python3 polybox_upload.py --mode dry-run
#python3 polybox_upload.py --mode upload
#python3 polybox_upload.py --mode upload --targets influenza
#python3 polybox_upload.py --mode dry-run --targets rsv

analysis_dir="/cluster/project/pangolin/resources/cowwid/for_communication/scripts"

python "$analysis_dir/rsv_and_iva_polybox_upload.py" --mode upload > >(tee rsv_and_iva_polybox_upload.log) 2>&1

conda deactivate
