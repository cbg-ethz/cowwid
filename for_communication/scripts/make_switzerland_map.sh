#!/bin/bash

eval "$(/cluster/project/pangolin/test_automation/miniconda3/bin/conda shell.bash hook)"

conda activate communication_env

python /cluster/project/pangolin/cowwid/for_communication/scripts/ww_cov_switzerland_map.py > ww_cov_switzerland_map.log 2>&1