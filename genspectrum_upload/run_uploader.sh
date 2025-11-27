#!/bin/bash
set -euo pipefail

eval "$(/cluster/project/pangolin/test_automation/miniconda3/bin/conda shell.bash hook)"
conda activate /cluster/project/pangolin/processes/genspectrum_upload/genspectrum_upload

#setup path
base_path="/cluster/project/pangolin/processes/genspectrum_upload"
config_file="${base_path}/WISE-mut-freq-data-uploader/config.yaml"
#config_file_test="${base_path}/WISE-mut-freq-data-uploader/config_test_upload.yaml"

RSVA_folder="/cluster/project/pangolin/processes/rsv/RSVA/working/MutationFrequencies"
RSVB_folder="/cluster/project/pangolin/processes/rsv/RSVB/working/MutationFrequencies"

IA_H1_folder="/cluster/project/pangolin/processes/influenza/IA_H1/working/mutation_frequencies"
IA_H3_folder="/cluster/project/pangolin/processes/influenza/IA_H3/working/mutation_frequencies"
IA_N1_folder="/cluster/project/pangolin/processes/influenza/IA_N1/working/mutation_frequencies"
IA_N2_folder="/cluster/project/pangolin/processes/influenza/IA_N2/working/mutation_frequencies"

#TODO: check if this filtering is still needed
#preprocess RSV if necessary (see repo docs): checked latest file, should not be neede anymore
#awk -F'\t' 'NR==1 || $2=="RSV-B"' 20250701_2427506364_EPI_ISL_412866_Mutations_Dashboard.tsv 

# Put them in an array
folders=(
  "$RSVA_folder"
  "$RSVB_folder"
  "$IA_H1_folder"
  "$IA_H3_folder"
  "$IA_N1_folder"
  "$IA_N2_folder"
)

for data_dir in "${folders[@]}"; do
    # check if path exists
    if [[ ! -d "$data_dir" ]]; then
        echo "Skipping: $data_dir (does not exist)"
        continue
    fi

    dedup_data_dir="${data_dir}/deduped"

    # Make sure the output folder exists
    mkdir -p "$dedup_data_dir"

    # for each file that has not yet been checked to contain duplicates, create a file in deduped folder
    for file in "$data_dir"/*Mutations_Dashboard.tsv; do
        if [[ ! -e "$file" ]]; then
            continue
        fi

      filename=$(basename "$file")
      deduped="$dedup_data_dir/${filename%.tsv}_deduped.tsv"

      # Skip if output already exists
      if [[ -f "$deduped" ]]; then
        echo "Skipping: $deduped already exists"
        continue
      fi

      # Print duplicate full lines (excluding header)
      echo "Duplicates in $file:"
      tail -n +2 "$file" | sort | uniq -d

      # Write header + deduped content
      { head -n 1 "$file"; tail -n +2 "$file" | sort | uniq; } > "$deduped"

      echo "Saved deduped to: $deduped"
    done

    # upload the deduplicated files

    #check if it is rsv or influenza
    if [[ "$data_dir" == *rsv* ]]; then
        organism="rsv"
    elif [[ "$data_dir" == *influenza* ]]; then
        organism="influenza"
    else
        echo "Organism could not be determined from input path."
        echo "${data_dir}"
        continue
    fi

    #run the upload
    echo "python ${base_path}/WISE-mut-freq-data-uploader/scripts/upload_data.py --data-folder ${dedup_data_dir} --config-file ${config} --organism ${organism}"
    #   UNCOMMENT THIS ONCE UPLOAD WILL START
    #python ${base_path}/WISE-mut-freq-data-uploader/scripts/upload_data.py --data-folder ${dedup_data_dir} --config-file ${config} --organism ${organism}

done


echo "Done."