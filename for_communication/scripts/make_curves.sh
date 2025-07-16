#!/bin/bash

eval "$(/cluster/project/pangolin/test_automation/miniconda3/bin/conda shell.bash hook)"

conda activate communication_env

python /cluster/project/pangolin/cowwid/for_communication/scripts/ww_cov_curves_v-pipe.py > ww_cov_curves_v-pipe.log 2>&1
#add here the merge_json.py script -->output of this file should be uploaded to wiseDB

python /cluster/project/pangolin/cowwid/for_communication/scripts/historical/merge_json.py \
"/cluster/project/pangolin/cowwid/for_communication/resources/curves_untracked_wwtps.json" \
"/cluster/project/pangolin/work-vp-test/variants/deconvoluted_upload.json" \
"/cluster/project/pangolin/cowwid/for_communication/output/ww_update_data_wisebd.json" \
 > merge_json.log 2>&1