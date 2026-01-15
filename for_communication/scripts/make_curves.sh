#!/bin/bash

eval "$(/cluster/project/pangolin/resources/miniconda3/condabin/conda shell.bash hook)"

conda activate communication_env

python /cluster/project/pangolin/resources/cowwid/for_communication/scripts/ww_cov_curves_v-pipe.py "/cluster/project/pangolin/resources/cowwid/for_communication/config/config.yaml" > >(tee ww_cov_curves_v-pipe.log) 2>&1
#add here the merge_json.py script -->output of this file should be uploaded to wiseDB

#'''
#def parse_args():
#    parser = argparse.ArgumentParser(
#        description="Merge two nested-JSON files into one with duplication checks.")
#    parser.add_argument('first_json', help='Path to the first input JSON file')
#    parser.add_argument('second_json', help='Path to the second input JSON file')
#    parser.add_argument('output_json', help='Path where the merged JSON will be written')
#    return parser.parse_args()
#'''
python /cluster/project/pangolin/resources/cowwid/for_communication/scripts/historical/merge_json.py \
"/cluster/project/pangolin/resources/cowwid/for_communication/resources/curves_untracked_wwtps.json" \
"/cluster/project/pangolin/processes/sars_cov_2/lollipop/variants/deconvoluted_upload.json" \
"/cluster/project/pangolin/resources/cowwid/for_communication/output/ww_update_data_wisebd.json" \
 > merge_json.log 2>&1
