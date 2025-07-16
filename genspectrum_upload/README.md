

**Once we start the regular upload again, some things have to be uncommented:**
- In /cluster/project/pangolin/genspectrum_upload/WISE-mut-freq-data-uploader/scripts/upload_data.py lines 321–325: for testing purposes the uploaded sequences have not been revised or approved — uncomment once new sequences are there.
- The empty batches still produce mutation frequency files in /cluster/project/pangolin/*/*/working/MutationFrequencies; this has to be adapted to avoid uploading whatever is there from the untracked time.
   - clean-up of irrelevant files
- In /cluster/project/pangolin/genspectrum_upload/run_uploader.sh the Python command to upload is commented out.
- TODO: add sun_uploader.sh to cowwid


# Overview

This script automates two main tasks for RSV and Influenza mutation frequency data:

1. **Deduplication:**
   It scans all `Mutations_Dashboard.tsv` files in specified working folders, checks for duplicate rows (excluding the header), prints duplicates for review, and writes a cleaned version to a `deduped/` subfolder.
2. **Upload:**
   After deduplication, the script uploads each cleaned dataset to the Wise-Loculus backend using the `upload_data.py` pipeline, with the correct `--organism` flag (`rsv` or `influenza`).


### Folder Structure

The script works with multiple predefined folders, for example:
```Bash
/cluster/project/pangolin/rsv_pipeline/RSVA/working/MutationFrequencies/
/cluster/project/pangolin/influenza_pipeline/IA_H1/working/MutationFrequencies/
...
```

It expects files named like:
```Bash
20250701_..._Mutations_Dashboard.tsv
```

Deduplicated outputs are written to:
```Bash
<source_folder>/deduped/
```

with filenames:
```Bash
<original_name>_deduped.tsv
```


### What the Script Does

1. **Loop over each folder**

   * Skip if folder doesn’t exist.
   * Create a `deduped/` subfolder if needed.

2. **Process each TSV**

   * Skip if no matching files.
   * If the deduped output already exists, skip reprocessing.
   * Print lines that appear more than once (excluding the header).
   * Write the header plus unique rows to the output.

3. **Determine organism type**

   * If folder path includes `rsv` → use `--organism rsv`
   * If folder path includes `influenza` → use `--organism influenza`
   * Skip folder if organism cannot be determined.

4. **Run the uploader**

   * Calls the Python `upload_data.py` script with:

     * `--data-folder` → the `deduped/` path
     * `--config-file` → your YAML config
     * `--organism` → `rsv` or `influenza`

5. **Safe to rerun**

   * Will not overwrite existing deduped files.
   * Will not re-upload unchanged folders if you comment out the Python call for dry runs.

### Tips

* You can safely run the script multiple times — it won’t reprocess files that are already deduped.
* Duplicates are printed to stdout so you can verify what was removed.
* Check that your `~/.netrc` or config file is set up correctly for authentication.
