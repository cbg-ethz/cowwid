#!/bin/bash

eval "$(/cluster/project/pangolin/test_automation/miniconda3/bin/conda shell.bash hook)"

conda activate communication_env

python /cluster/project/pangolin/cowwid/for_communication/scripts/ww_cov_uploader_v-pipe.py > ww_cov_uploader_v-pipe.log 2>&1