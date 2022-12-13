---
Date:	2022-12-12
Version:	0.9.1
---
# Wastewater reporting bioinformatics procedure

This repository os our _**Standard of Procedure**_, its puprose is to **document the current procedure** used to process wastewater.

Although it can transitionnally contain segments of code, these are merely notebooks showing temporary procedure in place (e.g.: uploading JSON formatted data to Cov-Spectrum).
Any computation (e.g.: variant deconvolution) will eventually be integrated into the software component we rely upon.

The current software includes:

 - [V-pipe](https://github.com/cbg-ethz/V-pipe) : Our main Virus NGS Analysis workflow
 - [cojac](https://github.com/cbg-ethz/cojac) : Tools for early detection based on combination of mutations
 - [LolliPop](https://github.com/cbg-ethz/LolliPop) : Tools for kernel-based deconvolution of variants



# CAVEAT: Pre-release

We're currenlty in the process of integrating most of the processing into V-pipe. 
A prototype of this integration is available in branch [ninjaturtles](https://github.com/cbg-ethz/V-pipe/tree/ninjaturtles).
This prototype still contains hard-coded value.

A config file-based version is coming next.



# Introduction

This readme file describes the procedure which is used since 2021-06-01 to prepare the wastewater-based SARS-CoV-2 prevalence display on [CoV-Spectrum](https://cov-spectrum.ethz.ch/story/wastewater-in-switzerland) as used on the page [Surveillance of SARS-CoV-2 genomic variants in wastewater](https://bsse.ethz.ch/cbg/research/computational-virology/sarscov2-variants-wastewater-surveillance.html). The main references are [doi:10.1038/s41564-022-01185-x](https://doi.org/10.1038/s41564-022-01185-x) (preprint: [doi:10.1101/2021.01.08.21249379](https://www.medrxiv.org/content/10.1101/2021.01.08.21249379)), and  [doi:10.1101/2022.11.02.22281825](https://doi.org/10.1101/2022.11.02.22281825).

It relies on V-pipe for most of the processing. The key steps are:

- [_Base processing_](#Base_processing): reads QC, alignments, etc. classic SARS-CoV-2 pipeline
- [_Cooccurrence analysis_](#Coocurrence_analysis): detect variats early using cooccurrence of mutations.
- [_Wastewater analysis_](#Wastewater_analysis): build variant curves, by deconvoluting for the variants found in the previous step.



# Base processing

Sample data is processed using the same pipeline configuration as currently used to process NGS data for the [Swiss SARS-CoV-2 Sequencing Consortium (S3C)](https://bsse.ethz.ch/cevo/research/sars-cov-2/swiss-sars-cov-2-sequencing-consortium.html).

*[NGS]: Next Generation Sequencing 
*[S3C]: Swiss SARS-CoV-2 Sequencing Consortium

## Installation

> **Summary:** all the necessary setup is already contained in the [pangolin](https://github.com/cbg-ethz/pangolin) repository. The repository needs to be cloned with its submodules, and the user needs to provide a bioconda installation in `pangolin/miniconda3` with packages _snakemake-minimal_ and _mamba_

The pipeline is configured as described in the repository [https://github.com/cbg-ethz/pangolin](https://github.com/cbg-ethz/pangolin) and its submodules.
- branch: [master](https://github.com/cbg-ethz/pangolin/tree/master), tip: [36fed5a89510372d384776d8ce714399521d65dd](https://github.com/cbg-ethz/pangolin/commit/36fed5a89510372d384776d8ce714399521d65dd)

Only the setup of V-pipe and cojac are described here.

### V-pipe setup

The V-pipe version provided by pangolin is set up following the same layout as produced by running the installer (it is equivalent to the results of running `bash quick_install.sh -b rubicon -p pangolin -w working`, see [tutorial](https://cbg-ethz.github.io/V-pipe/tutorial/sars-cov2/#install-v-pipe) and [V-pipe's main README.md](https://github.com/cbg-ethz/V-pipe/blob/master/README.md#using-quick-install-script)) and relies on the three directories:
- `pangolin/miniconda3` - **user-provided** installation of [miniconda3](https://bioconda.github.io/user/install.html) with packages _[snakemake-minimal](https://bioconda.github.io/recipes/snakemake/README.html)_ and _[mamba](https://anaconda.org/conda-forge/mamba)_ installed (see link for installation instruction).
- `pangolin/V-pipe` - installation of V-pipe as specified by the pangolin repository’s sub-module (simply checkout the submodule), namely:
  - repository: [https://github.com/cbg-ethz/V-pipe](https://github.com/cbg-ethz/V-pipe)
  - branch: [rubicon](https://github.com/cbg-ethz/V-pipe/tree/rubicon), tip: [e7cfbc5b06b8d3c51fdf231e99e0f0884415c384](https://github.com/cbg-ethz/V-pipe/commit/e7cfbc5b06b8d3c51fdf231e99e0f0884415c384)
- `pangolin/working` - working directory provided by the pangolin repository. Of note:
  - `pangolin/working/vpipe.config` - specific configuration used ([the virus-specific base configuration for SARS-CoV-2](https://github.com/cbg-ethz/V-pipe/blob/master/config/sars-cov-2.yaml) relies on [bwa](http://bio-bwa.sourceforge.net/) for alignment with reference [NC_045512](https://www.ncbi.nlm.nih.gov/nuccore/NC_045512) and [ShoRAH](https://github.com/cbg-ethz/shorah) for SNV and local haplotype calling. In addition, the resource parameters have been fine-tuned to allow the processing of very large cohorts).
  - `pangolin/working/`_*_`.bsub` - jobs used to perform the processing

*[SNV]: Single Nucleotide Variant

This V-pipe setup will store snakemake environments in `pangolin/snake-envs`. It is possible to pre-download them in advance by running `cd pangolin/V-pipe; ./vpipe --jobs 16 --conda-create-envs-only` (see [tutorial](https://cbg-ethz.github.io/V-pipe/tutorial/sars-cov2/#running-v-pipe-on-the-cluster)). On our cluster, this is performed by the command `pangolin/working/create_envs` which also takes care of HTTP proxy.

## Processing raw-reads with V-pipe

V-pipe takes care of performing quality controls, read filtering, alignments and tallying basecounts. More details about the internal functioning of V-pipe can be found in its primary publication [doi:10.1093/bioinformatics/btab015](https://doi.org/10.1093/bioinformatics/btab015).

### Inputs

V-pipe expects its input in subdirectories of `pangolin/working/samples` following a two-level hierarchy, and a 3-column TSV file `pangolin/working/samples.tsv`, as demonstrated in the [tutorial](https://cbg-ethz.github.io/V-pipe/tutorial/sars-cov2/#preparing-a-small-dataset).

In the current procedure, this is provided autonomously by the setup used for S3C, and is similar to the output generated by scripts provided in `pangolin/sort_samples_dumb` and `pangolin/sort_samples_demultiplexstats`.

The present procedure relies on the wastewater from Eawag samples following this naming schema, specifically providing a two-digit wastewater treatment plant (WWTP), and a sampling date:

*[WWTP]: Wastewater Treatment Plant

```
┌──────────────── Wastewater Treatment Plant:
│                  05 - CDA Lugano
│                  10 - ARA Werdhölzli in Zurich
│                  12 - STEP Vidy in Lausanne
│                  17 - ARA Chur
│                  19 - ARA Altenrhein
│                  25 - ARA Sensetal 
│  ┌───────────── Date
│  │          ┌── Sample properties
┴─ ┴───────── ┴─
09_2020_03_24_B
10_2020_03_03_B
10_2020_03_24_A
10_2020_04_26_30kd
```

The Kanton Zürich data follow a different schema:

```
       ┌───────── Date: YYmmdd)
       │      ┌── (optionnal: alternate kit)
       ┴───── ┴─
KLZHCov210815_2
```

Basel has another schema:
```
  ┌──────────────────── (internal id)
  │      ┌───────────── Date: YYYY-mm-dd
  │      │          ┌── (optionnal: alternate kit)
  ┴───── ┴───────── ┴─
Ba210449_2021-11-10
```

- These name can be automatically parsed by regular expressions defined inside `regex.yaml`.
- A `ww_locations.tsv` look-up table maps WWTP codes to fullnames.

(see [Wastewater analysis](#Wastewater_analysis) below).

### Configuration

The configuration for running V-pipe resides in the file `pangolin/working/vpipe.config`. The configuration as used presently in the procedure is provided in the repository pangolin as mentioned in [installation](#installation).

### Execution

In the directory `pangolin/working`, submit the job `vpipe-noshorah.bsub` (LSF) or `vpipe-noshorah.sbatch` (SLURM) to the cluster.

This will run the initial steps of V-pipe but stop before calling SNV and local haplotypes with ShoRAH.



# Coocurrence analysis

> **Note:** cojac _**is now**_ part of V-pipe.

## Installation

> **Note:** this branch currenlty has hard-coded value and is not easily portable to other deployment without manually editing the rules inside [signatures.smk](https://github.com/cbg-ethz/V-pipe/blob/ninjaturtles/workflow/rules/signatures.smk)

Processing uses the V-pipe.
 - branch: [ninjaturtles](https://github.com/cbg-ethz/V-pipe/tree/ninjaturtles), tip: [c2ac8adac6b027f5904e870239279f63268b3755](https://github.com/cbg-ethz/V-pipe/commit/c2ac8adac6b027f5904e870239279f63268b3755)

A cojac version is provided by pangolin in this directory:

- `pangolin/cojac`  - installation of cojac as specified by the pangolin repository’s sub-module (simply checkout the submodule), namely:
  - repository: [https://github.com/cbg-ethz/cojac](https://github.com/cbg-ethz/cojac)
  - branch: [dev](https://github.com/cbg-ethz/cojac/tree/dev), tip: [d4aaa470866876c6c6f66e526e61503ba65a8e44](https://github.com/cbg-ethz/cojac/commit/d4aaa470866876c6c6f66e526e61503ba65a8e44)

Because the above is still in an experimental state, we run in a separate working area (`work-vp-test/` instead of `working/`). Scripts assist handling these directories.

## Analysing cooccurrence with V-pipe

The following document assumes user have already performed the base analysis with V-pipe, but because Snakemake is depedency-based, it is also possible to automatically regenerate any intermediate output.

### Inputs

- `/pangolin/work-vp-test/samples.wastewateronly.tsv` - TSV table of the samples (the subset samples.tsv with wastewater samples)
- `/pangolin/work-vp-test/reference/voc/`_*_`.yaml` - definition of the variants
  - a copy of this collection of YAML is in the [`voc/` subdirectory](voc/)
  - TODO procedure for creating and curating new one
- `/pangolin/work-vp-test/reference/primers.yaml` and `/pangolin/work-vp-test/reference/primers/` : multiplex PCR amplicon definitions
  - a copy of this is provided in [SARS-CoV-2 specific resource packaged as part of V-pipe](https://github.com/cbg-ethz/V-pipe/tree/master/resources/sars-cov-2)
  - at the time of writing, this includes ARTIC protocol version 3, 4, and 4.1
  - documentation about amplicons is found in [section _amplicons_ of the config's README file](https://github.com/cbg-ethz/V-pipe/tree/master/config#amplicon-protocols)
- `/pangolin/work-vp-test/work-vp-results/`_*_`/`_*_`/alignment/REF_aln_trim.bam` - Alignments generated by V-pipe (see base processing above).
  - Note that analysis is run on the trimmed alignments for convenience, but due to its nature (it's looking at the exact amplicons of the multiplex PCR), it's not affected by trimming.

### Execution

> **Summary:** actual processing is handled by V-pipe, here we document the exact commands that we use locally on our cluster.

Because the above is still in an experimental state, we run in a separate working area (`work-vp-test/` instead of `working/`).

In the directory `pangolin`, there is a tool called `cowabunga.sh` (that can assist in preparing data for running V-pipe).

- run `./cowabunga.sh autoaddwastewater`
  - this adds the wastewater samples at top of file `/pangolin/work-vp-test/samples.wastewateronly.tsv`
- run `./cowabunga.sh bring_results`
  - this creates the necessary hardlinks inside `/pangolin/work-vp-test/results` so that V-pipe can reuse the alignments previously done as part of the base procesing.
- submit V-pipe to the cluster with SLURM:
  - for interactive output on the terminal:
    ```bash
    cd work-vp-test/
    srun --pty --job-name=COWWID-vpipe --mem-per-cpu=4096 --mail-type=END --mail-user="ivan.topolsky@bsse.ethz.ch" --time=23:00:00 -- vpipe-test.sbatch 
    ```
  - for batch submisison:
    ```bash
    cd work-vp-test/
    sbatch vpipe-test.sbatch 
    ```
  - **Note:** this will run both the cooccurrence and the deconvolution, see content of `vpipe-test.sbatch`:
    ```bash
    …
    exec ./vpipe --profile ${SNAKEMAKE_PROFILE} --restart-times=0 \
        allCooc tallymut deconvolution \
        --groups sigmut=group0 cooc=group1 \
        --group-components group0=10 group1=5
    ```

### Output
  
- `/pangolin/work-vp-test/variants/amplicons.v`_*_`.yaml` - amplicon description (generated from cojac's definitions) 
- `/pangolin/work-vp-test/results/`_*_`/`_*_`/signatures/cooc.yaml` - internal cojac format with coocurrences

## Interpretation of the results

### Input

First obtain all the cooccurrences of the most recent amplicon protocol:

```bash
./cowabunga.sh fetch_cooc v41
```

This will generate `work-vp-test/cooc.v41.yaml`

### Execution

Then refer to the [README.md](https://github.com/cbg-ethz/cojac/tree/dev#display-data-on-terminal) to display output:

```bash
# on the terminal of your laptop:
cojac cooc-colourmut --amplicons amplicons.v41.yaml --yaml cooc.v41.yaml | less -SR

# on our cluster
mamba acticate 
test/cojac-wrapper cooc-colourmut --amplicons work-vp-test/variants/amplicons.v41.yaml --yaml work-vp-test/cooc.v41.yaml | less -SR
```

**Advices:**

- Based on the curate information gathered from the background on Cov-Spectrum, you might want to edit and make a subset out of amplicon.v41.yaml that concentrates on the interesting amplicons and mutations for the variants you are seeking to detect early.
- `less -SR` will enable horizontal scrolling and will support the ANSI colour codes
- alternatively from the terminal output, you could try pubmut for other table display formats, or tabmut for tabular data that you could ingest into your favourite display tool

### Output

Manually edit and adapt `work-vp-test/variants.yaml` and `work-vp-test/var_dates.yaml` to require deconvolution to include these newly detected variants (see next section "Wastewater_analysis").



# Wastewater analysis

> **Note:** 
> - LolliPop _**is now**_ part of V-pipe.
> - Due to issues, we are temporarily building the curves with a Notebook instead of the command-line interface of LolliPop

## Installation

> **Note:** this branch currenlty has hard-coded value and is not easily portable to other deployment without manually editing the rules inside [signatures.smk](https://github.com/cbg-ethz/V-pipe/blob/ninjaturtles/workflow/rules/signatures.smk)

Processing uses the V-pipe.
 - branch: [ninjaturtles](https://github.com/cbg-ethz/V-pipe/tree/ninjaturtles), tip: [c2ac8adac6b027f5904e870239279f63268b3755](https://github.com/cbg-ethz/V-pipe/commit/c2ac8adac6b027f5904e870239279f63268b3755)

A LolliPop version is temporarily installed iside:

- `pangolin/test/LolliPop`:
  - repository: [https://github.com/cbg-ethz/cojac](https://github.com/cbg-ethz/LolliPop)
  - branch: [main](https://github.com/cbg-ethz/LolliPop/tree/main), tip: [6b4495e1fdc6824ecdccfef866bbd2b11b200105](https://github.com/cbg-ethz/LolliPop/commit/6b4495e1fdc6824ecdccfef866bbd2b11b200105)

Because the above is still in an experimental state, we run in a separate working area (`work-vp-test/` instead of `working/`). Scripts assist handling these directories.

## Configuration

You still need to update manually `work-vp-test/variants.yaml` and `work-vp-test/var_dates.yaml` and re-run V-pipe if coocurrences have revealed early presence of another variant.

- `/pangolin/work-vp-test/variant_config.yaml` -  general informations (variants, locations) used for deconvolution
  - _locations_list_ (fomerly _cities_list_): full names of the locations for which to generate curves (see right column of `ww_locations.tsv`).
  - _variants_list_ - full list of [PANGO lineages](https://cov-lineages.org/) plotted (as specified in the "_pangolin:_" field of the `voc/`_*_`.yaml` descriptions).
  - _variants_pangolin_ - dictionary mapping short names to the official pango lineages (see: "_pangolin:_" and "_short:_" fields in the `voc/`_*_`.yaml` description)
  - _variants_not_reported_ lists variants which will be not part of the regression and will be removed before the ressampling
  - _start_date_:  first  date for the deconvolution
  - _to_drop_: category of mutation to skip from tallymut (e.g.: subset),
- `/pangolin/work-vp-test/var_dates.yaml` - which variants LolliPop needs to deconvolute for over which period of time.
  - at each starting date, list the combination of variants that will be deconvoluted for the next period of time, as determined by cojac in the section above.

Configuration file `regex.yaml` defines regular expressions that help parse the samples names as per section [Processing raw-reads with V-pipe](#Processing_raw-reads_with_V-pipe) above.

- `sample` (and optionnally `batch`) define regular expressions that are run against the first (and optionnally second) column of V-pipe's `samples.tsv`. They define the following named-groups
  - `location`: this named-group gives the code for the location (e.g.: Ewag's number code, `Ba`, `KLZH`, etc.)
  - `year`: year (in `YYYY` or `YY` format. `YY` are automatically expanded to `20YY` -  Yes, I am optimistic with the duration of this pandemic. Or pessimistic with long term use of V-pipe after the turn of century).
  - `month`: month
  - `day`: day
  - `date`: an alternative to the year/month/day groups, if dates aren't in a standard format.
  - regex are parsed with the Python regex library, and multiple named groups can use the same name.
    You can thus have a contstruction where you use `|` to give multiple alternative as long as each provide named-groups `location` and either  `year`, `month`, and `day` or `date`:
     ```regex
     (?:(?P<location>\d+)_(?P<year>20\d{2})_(?:(?:(?P<month>[01]?\d)_(?P<day>[0-3]?\d))|(?:R_(?P<repeat>\d+))))|^(?:(?P<location>KLZHCo[vV])(?P<year>\d{2})(?P<month>[01]?\d)(?P<day>[0-3]?\d)(?:_(?P<location_extra>\w+))?)|^(?:(?P<location>B[aA])(?P<BAsam>\d{6})(?:[-_](?P<year>20\d{2})-(?P<month>[01]?\d)-(?P<day>[0-3]?\d))?)
     ``` 
- `datefmt`: [strftime/strptime format string](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes) to be used on regex named group `date` (e.g.: use `"%Y%m%d"` to parse YYYYMMDD).
  -  This is most useful for date formats that don't split nicely into the ` year`, `month`, and `day` regex  named groups: e.g. if your date format uses week number, day of the week, or day of year.
     In that case, write a regular expression that provides a named-group `date`, and then use, e.g., `%W` or `%-d` in your ` datefmt`.

A look-up table `ww_locations.tsv` maps the location code (see `location` regex named group in the previous file) to their full description.



## Analysing wastewater with V-pipe

The following document assumes user have already performed the base analysis and the cooccurrence with V-pipe, but because Snakemake is depedency-based, it is also possible to automatically regenerate any intermediate output.

### Inputs

- `/pangolin/work-vp-test/samples.wastewateronly.tsv` - TSV table of the samples (the subset samples.tsv with wastewater samples)
- `/pangolin/work-vp-test/reference/voc/`_*_`.yaml` - definition of the variants
  - a copy of this collection of YAML is in the [`voc/` subdirectory](voc/)
  - TODO procedure for creating and curating new one
- `/pangolin/work-vp-test/work-vp-results/`_*_`/`_*_`/alignment/basecnt.tsv.gz` - Basecounts (pileup-like coverage plot) generated by V-pipe (see base processing above).
- `/pangolin/working/references/gffs/Genes_NC_045512.2.GFF3` - genes table  (used to add Genenames into the tally mut).

### Execution

> **Summary:** actual processing is handled by V-pipe, here we document the exact commands that we use locally on our cluster.

Because the above is still in an experimental state, we run in a separate working area (`work-vp-test/` instead of `working/`).

In the directory `pangolin`, there is a tool called `cowabunga.sh` (that can assist in preparing data for running V-pipe).

- run `./cowabunga.sh autoaddwastewater`
  - this adds the wastewater samples at top of file `/pangolin/work-vp-test/samples.wastewateronly.tsv`
- run `./cowabunga.sh bring_results`
  - this creates the necessary hardlinks inside `/pangolin/work-vp-test/results` so that V-pipe can reuse the alignments previously done as part of the base procesing.
- submit V-pipe to the cluster with SLURM:
  - for interactive output on the terminal:
    ```bash
    cd work-vp-test/
    srun --pty --job-name=COWWID-vpipe --mem-per-cpu=4096 --mail-type=END --mail-user="ivan.topolsky@bsse.ethz.ch" --time=23:00:00 -- vpipe-test.sbatch 
    ```
  - for batch submisison:
    ```bash
    cd work-vp-test/
    sbatch vpipe-test.sbatch 
    ```
  - **Note:** this will run both the cooccurrence and the deconvolution, see content of `vpipe-test.sbatch`:
    ```bash
    …
    exec ./vpipe --profile ${SNAKEMAKE_PROFILE} --restart-times=0 \
        allCooc tallymut deconvolution \
        --groups sigmut=group0 cooc=group1 \
        --group-components group0=10 group1=5
    ```

### Output

- `/pangolin/work-vp-test/variants/tallymut.tsv.zstd` - table of all variant-characteristic mutations found
- `/pangolin/work-vp-test/variants/deconvolute.tsv.zstd`  - output of the deconvolution

> **Note** thre are issue with the error margins generated by the current deconvolution methods


## Generate the plot: Heatmaps

**NOTE** since switching to the exhaustive mutation list, the mutaiton heatmap display has become unusable and is not generated anymore.

**TODO** better visualisation of the presence of variants.


## Interpretation of results

> **Note** thre are issue with the error margins generated by the current deconvolution methods directly setup inside V-pipe

Notebook `WsSmoothing_legacy.ipynb` is temporarily used to do a bootstrap-based deconvolution using the files output by V-pipe.

> **Note:** unlike the notebook `pangolin/cojac/notebooks/ww_smoothing.ipynb` used in the article, posterior probabilities of the local haplotype generated by ShoRAH are not taken into account, and the curves are built using a kernel based deconvolution which is both more robust against variants that share mutations in their exhaustive lists, and able to leverage the time component to  compensate the extreme over-dispestion of typical wastewater samples.

### Input

- `./work-vp-test/variants//tallymut.tsv.zst` - table of all variant-characteristic mutations generated by V-pipe

### Configuration

Configuration of the notebook relies on the same files `work-vp-test/variants.yaml` and `work-vp-test/var_dates.yaml` as used by V-pipe.

(This configuration was formerly specified in the cell in the section titled "Globals").

Input files path can also be specified in Globals.

### Execution

- Run all cells until the end of section "covSPECTRUM export".
- Inspect the plots generated by the Notebook.

## Output

- `ww_update_data_smooth_kernel_lin.json`: output generated with the fast linear.
- `ww_update_data_smooth_kernel_rob.json`: robust full deconvolution

## Upload

Notebook - `ww_cov_uploader.ipynb` - handles the upload onto CoV-Spectrum itself

### Input
- `ww_update_data_heatmap.json` - a file with uploadable data for CoV-Spectrum that contains the heatmaps.
  - Note that this file isn't updated anymore, due to the excessively long exhaustive list breaking the output.
- `ww_update_data_smooth_kernel_rob.json`: robust full deconvolution

In addition the actual upload itself requires database credentials. These are currently retrieved from `~/.netrc` standard Unix credential storage, but alternative methods are commented-out in the cells under the "Upload to Cov-Spectrum" section.

### Execution

- Run cells in section "Upload to Cov-Spectrum" with the following:
  - the cell tagged "`## Abort DB update !`" is used only to abort the update and rollback to the initial state in case or problems. It is skipped otherwise.
  - the cell tagged "`## Save to DB !`" is used instead to make the changes permanent in the database.

### Outputs

The curves are now load up on [CoV-Spectrum](https://cov-spectrum.ethz.ch/story/wastewater-in-switzerland).



# Comments regarding the current procedure

Due to the excessively long list of mutations generated from Cov-Spectrum, and the excessively complex amplicon-cooccurrence that results of it, heatmaps aren't displayed anymore as they are unreadable. We are working toward fixing this.

Unlike the pre-print [doi:10.1101/2021.01.08.21249379](https://www.medrxiv.org/content/10.1101/2021.01.08.21249379), the current procedure skips running ShoRAH:  Instead of trying to build confidence at the level of single mutation, current method in LolliPop relies instead on a kernel-based deconvolution that enables us to leverage the time component and gives us higher confidence in our call despite drop-outs and extreme dispestion of data.

As an additional measure to avoid outliers, mutations which aren’t exclusive to a single variant aren’t taken into account in B.1.351/beta and P.1/gamma.
E.g.: mutation nuc: A23063T (aa: N501Y) will not be used there as it is also present in B.1.1.7/alpha and would artificially inflate the numbers.
Other similar signature mutations which do not follow the general trend of a variant are also filtered out.

'Undetermined' is defined by the absence of signature mutations, thus it doesn't have its own heatmap (it is defined by the complement of all other heatmaps).

The values of the curves are currently clipped to the [0;1] interval as the smoothing can currently generate values outside this range.

As the procedure is improved these caveats are subject to change in future revision of this document.
