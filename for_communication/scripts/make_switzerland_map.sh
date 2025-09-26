#!/bin/bash

eval "$(/cluster/project/pangolin/resources/miniconda3/bin/conda shell.bash hook)"

conda activate communication_env

python /cluster/project/pangolin/resources/cowwid/for_communication/scripts/ww_cov_switzerland_map.py > >(tee ww_cov_switzerland_map.log) 2>&1
