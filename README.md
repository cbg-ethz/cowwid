---
Date:	2023-04-08
Version:	0.9.2
---
# Wastewater reporting bioinformatics procedure

This repository os our _**Standard of Procedure**_, its purpose is to **document the current procedure** used to process wastewater.

Although it can transitionally contain segments of code, these are merely notebooks showing temporary procedures in place or results visualization (e.g.: uploading JSON formatted data to Cov-Spectrum).
Any computation (e.g.: variants deconvolution) are usually integrated into the software component we rely upon.

The current software includes:

 - [V-pipe](https://github.com/cbg-ethz/V-pipe): Our main Virus NGS Analysis workflow.
 - [cojac](https://github.com/cbg-ethz/cojac): Integrated into V-pipe, component tool for early detection based on combination of mutations
 - [LolliPop](https://github.com/cbg-ethz/LolliPop): Integrated into V-pipe, component tool for kernel-based deconvolution of variants



# CAVEAT: Pre-release

We're currently in the process of integrating most of the processing into V-pipe.
A prototype of this integration is available in branch [ninjaturtles](https://github.com/cbg-ethz/V-pipe/tree/ninjaturtles), and the latest version is now config file-based and can be adapted to other sites.

There is no tutorial, yet. In the mean time, a [draft _HOWTO_](https://gist.github.com/DrYak/e28d5d523e644ea455748d540a32ad4d) can help you understand the details and deploy V-pipe in your own setting.



# Introduction

This readme file describes the procedure which is used since 2023-04-08 to prepare the wastewater-based SARS-CoV-2 prevalence display on [CoV-Spectrum](https://cov-spectrum.ethz.ch/story/wastewater-in-switzerland) and provide the data to  [BAG/FOPH](https://www.covid19.admin.ch/en/epidemiologic/waste-water). The main references are [doi:10.1038/s41564-022-01185-x](https://doi.org/10.1038/s41564-022-01185-x) (preprint: [doi:10.1101/2021.01.08.21249379](https://www.medrxiv.org/content/10.1101/2021.01.08.21249379)), and  [doi:10.1101/2022.11.02.22281825](https://doi.org/10.1101/2022.11.02.22281825).

It relies on V-pipe for most of the processing. The key steps are:

- [_Base processing_](#base-processing): reads QC, alignments, etc. classic SARS-CoV-2 pipeline
- [_Cooccurrence analysis_](#coocurrence-analysis): detect variants early using cooccurrences of mutations.
- [_Wastewater analysis_](#wastewater-analysis): build variant curves, by deconvoluting for the variants found in the previous step.

A separate procedure documents the steps to [add a new variant](#add-a-new-variant).



# Add a New Variant

**TODO** (TO BE DOCUMENTED, [check HOWTO for now](https://gist.github.com/DrYak/e28d5d523e644ea455748d540a32ad4d#signatures-for-variants))



# Base processing

Sample data is processed using the same pipeline configuration as currently used to process NGS data for the [Swiss SARS-CoV-2 Sequencing Consortium (S3C)](https://bsse.ethz.ch/cevo/research/sars-cov-2/swiss-sars-cov-2-sequencing-consortium.html).

> **Note** as the S3C project is being sunsetted, and as the wastewater workflow matures, both sub-parts will be eventually merge into a single process, as documented in the HOWTO.

*[NGS]: Next Generation Sequencing
*[S3C]: Swiss SARS-CoV-2 Sequencing Consortium

## Installation

> **Summary:** all the necessary setup is already contained in the [pangolin](https://github.com/cbg-ethz/pangolin) repository. The repository needs to be cloned with its submodules, and the user needs to provide a bioconda installation in `pangolin/miniconda3` with packages _snakemake-minimal_ and _mamba_

The pipeline is configured as described in the repository [https://github.com/cbg-ethz/pangolin](https://github.com/cbg-ethz/pangolin) and its submodules.
- branch: [master](https://github.com/cbg-ethz/pangolin/tree/master), tip: [1c819ee42b5e112b8db07bc79d38f793981530dd](https://github.com/cbg-ethz/pangolin/commit/1c819ee42b5e112b8db07bc79d38f793981530dd)

### V-pipe setup

The V-pipe version provided by pangolin is set up following the same layout as produced by running the installer (it is equivalent to the results of running `bash quick_install.sh -b rubicon -p pangolin -w working`, see [tutorial](https://github.com/cbg-ethz/V-pipe/blob/master/docs/README.md) and [V-pipe's main README.md](https://github.com/cbg-ethz/V-pipe/blob/master/README.md#using-quick-install-script)) and relies on the three directories:
- `pangolin/miniconda3` -- **user-provided** installation of [miniconda3](https://bioconda.github.io/user/install.html) with packages _[snakemake-minimal](https://bioconda.github.io/recipes/snakemake/README.html)_ and _[mamba](https://anaconda.org/conda-forge/mamba)_ installed (see link for installation instruction).
- `pangolin/V-pipe` -- installation of V-pipe as specified by the pangolin repository’s sub-module (simply checkout the submodule), namely:
  - repository: [https://github.com/cbg-ethz/V-pipe](https://github.com/cbg-ethz/V-pipe)
  - branch: [rubicon](https://github.com/cbg-ethz/V-pipe/tree/rubicon), tip: [e8be5f1fad7a970e3299e142f329f037f3890fe4](https://github.com/cbg-ethz/V-pipe/commit/e8be5f1fad7a970e3299e142f329f037f3890fe4)
- `pangolin/working` -- working directory provided by the pangolin repository. Of note:
  - `pangolin/working/vpipe.config` -- specific configuration used ([the virus-specific base configuration for SARS-CoV-2](https://github.com/cbg-ethz/V-pipe/blob/master/config/sars-cov-2.yaml) relies on [bwa](http://bio-bwa.sourceforge.net/) for alignment with reference [NC_045512](https://www.ncbi.nlm.nih.gov/nuccore/NC_045512) and [ShoRAH](https://github.com/cbg-ethz/shorah) for SNV and local haplotype calling. In addition, the resource parameters have been fine-tuned to allow the processing of very large cohorts).
  - `pangolin/working/`_*_`.sbatch` and `.bsub`- jobs used to perform the processing

*[SNV]: Single Nucleotide Variant

This V-pipe setup will store snakemake environments in `pangolin/snake-envs`. It is possible to pre-download them in advance by running `cd pangolin/V-pipe; ./vpipe --jobs 16 --conda-create-envs-only` (see [tutorial](https://cbg-ethz.github.io/V-pipe/tutorial/sars-cov2/#running-v-pipe-on-the-cluster)). On our cluster, this is performed by the command `pangolin/working/create_envs` which also takes care of HTTP proxy.

## Processing raw-reads with V-pipe

V-pipe takes care of performing quality controls, read filtering, alignments and tallying basecounts. More details about the internal functioning of V-pipe can be found in its primary publication [doi:10.1093/bioinformatics/btab015](https://doi.org/10.1093/bioinformatics/btab015).

### Inputs

V-pipe expects its input in subdirectories of `pangolin/working/samples` following a two-level hierarchy, and a 3-column TSV file `pangolin/working/samples.tsv`, as demonstrated in the [tutorial](https://github.com/cbg-ethz/V-pipe/blob/master/docs/tutorial_sarscov2.md).

> **Note** for legacy reasons, we are still currently relying on a different layout than modern Snakemake Workflow recommendations and V-pipe official defaults:
> - we process everything in the samples `samples/` directory, (V-pipe & Snakemake default: input goes in `samples/`, output foes in `results/`)
> - we keep a copy of raw reads in top-level `sampleset/` that we hard-link into `working/samples/` (V-pipe & Snakemake default: separate input directory can be directly accessed).
> - cohort-wide results (reports, etc. that aren't specific to a single samples) are currently in `variants/` (V-pipe default: goes into the base of `results/`)
> - we still rely on the legacy INI-like format used by older V-pipe 1.0 and 2.0 (Snakemake default: uses `config.yaml`)

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
       │      ┌── (optional: alternate kit)
       ┴───── ┴─
KLZHCov210815_2
```

Basel has another schema:
```
  ┌──────────────────── (internal id)
  │      ┌───────────── Date: YYYY-mm-dd
  │      │          ┌── (optional: alternate kit)
  ┴───── ┴───────── ┴─
Ba210449_2021-11-10
```

- These name can be automatically parsed by regular expressions defined inside `regex.yaml`.
- A `ww_locations.tsv` look-up table maps WWTP codes to full names.

(see [Wastewater analysis](#Wastewater_analysis) below).

### Configuration

The configuration for running V-pipe resides in the file `pangolin/working/vpipe.config`. The configuration as used presently in the procedure is provided in the repository pangolin as mentioned in [installation](#installation).

### Execution

In the directory `pangolin/working`, submit the job `vpipe-noshorah.bsub` (LSF) or `vpipe-noshorah.sbatch` (SLURM) to the cluster.

This will run the initial steps of V-pipe but stop before calling SNV and local haplotypes with ShoRAH.



# Coocurrence analysis

> **Note** cojac _**is now**_ part of V-pipe.

## Installation

Processing uses the V-pipe.
- branch: [ninjaturtles](https://github.com/cbg-ethz/V-pipe/tree/ninjaturtles), tip: [e8be5f1fad7a970e3299e142f329f037f3890fe4](https://github.com/cbg-ethz/V-pipe/commit/e8be5f1fad7a970e3299e142f329f037f3890fe4)
  - this branch relies on COJAC 0.9 released on [bioconda](https://bioconda.github.io/recipes/cojac/README.html).

Because the above is still in an experimental state, we run in a separate working area (`work-vp-test/` instead of `working/`), the prototype branch is in the [`V-pipe-test`](pangolin/V-pipe-test) submodule of repo pangolin. Scripts ([`cowabunga.sh`](https://github.com/cbg-ethz/pangolin/blob/master/cowabunga.sh)) assist handling these directories.

## Analyzing cooccurrence with V-pipe

The following document assumes user have already performed the base analysis with V-pipe, but because Snakemake is dependency-based, it is also possible to automatically regenerate any intermediate output.

### Inputs

(The script will help you generate those)

- `/pangolin/work-vp-test/samples.wastewateronly.tsv` -- TSV table of the samples (the subset samples.tsv with wastewater samples)
- `/pangolin/work-vp-test/reference/voc/`_*_`.yaml` -- definition of the variants
  - a copy of this collection of YAML is in the [`voc/` subdirectory](voc/)
  - TODO procedure for creating and curating new one
- `/pangolin/work-vp-test/reference/primers.yaml` and `/pangolin/work-vp-test/reference/primers/` : multiplex PCR amplicon definitions
  - a copy of this is provided in [SARS-CoV-2 specific resource packaged as part of V-pipe](https://github.com/cbg-ethz/V-pipe/tree/master/resources/sars-cov-2)
  - at the time of writing, this includes ARTIC protocol version 3, 4, and 4.1
  - documentation about amplicons is found in [section _amplicons_ of the config's README file](https://github.com/cbg-ethz/V-pipe/tree/master/config#amplicon-protocols)
- `/pangolin/work-vp-test/results/`_*_`/`_*_`/alignment/REF_aln_trim.bam` -- Alignments generated by V-pipe (see [base processing](#base-processing) above).
  - Note that analysis is run on the trimmed alignments for convenience, but due to its nature (it's looking at the exact amplicons of the multiplex PCR), it's not affected by trimming.

### Execution

> **Summary:** actual processing is handled by V-pipe, here we document the exact commands that we use locally on our cluster.

Because the above is still in an experimental state, we run in a separate working area (`work-vp-test/` instead of `working/`, and the V-pip installed in `V-pipe-test/` instead of `V-pipe/`).

In the directory `pangolin`, there is a tool called `cowabunga.sh` (that can assist in preparing data for running V-pipe).

- run `./cowabunga.sh autoaddwastewater`
  - this adds the wastewater samples at top of file `/pangolin/work-vp-test/samples.wastewateronly.tsv`, based on the project ID used by FGCZ.
- run `./cowabunga.sh bring_results`
  - this creates the necessary hard-links inside `/pangolin/work-vp-test/results` so that V-pipe can reuse the alignments previously done as part of the [base processing](#base-processing).
- submit V-pipe to the cluster with SLURM:
  - for interactive output on the terminal:
    ```bash
    cd work-vp-test/
    srun --pty --job-name=COWWID-vpipe --mem-per-cpu=4096 --mail-type=END --mail-user="ivan.topolsky@bsse.ethz.ch" --time=23:00:00 -- vpipe-test.sbatch
    ```
  - for batch submission:
    ```bash
    cd work-vp-test/
    sbatch vpipe-test.sbatch
    ```
  - > **Note** this will run both the cooccurrence and the deconvolution, see content of `vpipe-test.sbatch`:
    ```bash
    …
    exec ./vpipe --profile ${SNAKEMAKE_PROFILE} --restart-times=0 \
        allCooc variants/cohort_cooc_report.v41.csv tallymut deconvolution \
        --groups sigmut=group0 cooc=group1 \
        --group-components group0=10 group1=5
    ```
    to only run COJAC use rules such as:
    - `variants/amplicon.v41.yaml` -- amplicon description for protocol Artic v4.1.
    - `allCooc` -- runs COJAC on all samples.
    - `variants/cohort_cooc_report.v41.csv` -- assembles all COJAC results from all samples processed with Artic v4.1 into a table as featured in the additonnal materials of articles.

### Output

- `/pangolin/work-vp-test/variants/amplicons.v`_*_`.yaml` -- amplicon description (generated from cojac's definitions)
- `/pangolin/work-vp-test/results/`_*_`/`_*_`/signatures/cooc.yaml` -- internal cojac format with coocurrences
- `/pangolin/work-vp-test/variants/cohort_cooc.`_*_`.yaml` and `.csv` -- COJAC results of all samples, aggregated by protocol.
- `/pangolin/work-vp-test/variants/cohort_cooc_report.`_*_`.csv` -- COJAC results, in a publication-like table

## Interpretation of the results

You can load _cohort_cooc_report.v41.csv_ in Libre-Calc, Excel, etc. or, for visualization on the terminal….

### Execution

…refer to [COJAC's README.md](https://github.com/cbg-ethz/cojac/tree/dev#display-data-on-terminal) to display output:

```bash
# on the terminal of your laptop:
cojac cooc-colourmut --amplicons amplicons.v41.yaml --yaml cooc.v41.yaml | less -SR
```

**Advices:**

- Based on the curate information gathered from the background on Cov-Spectrum, you might want to edit and make a subset out of amplicon.v41.yaml that concentrates on the interesting amplicons and mutations for the variants you are seeking to detect early.
- `less -SR` will enable horizontal scrolling and will support the ANSI colour codes

### Output

Manually edit and adapt `work-vp-test/var_dates.yaml` (the list of all variant will be correctly auto-guess, no need to use one in  `work-vp-test/variants_config.yaml` )  to require deconvolution to include these newly detected variants (see next section "[Wastewater analysis](#wastewater-analysis)").



# Wastewater analysis

> **Note**
> - LolliPop _**is now**_ part of V-pipe and runs the deconvolution
> - unlike the notebook `cojac/notebooks/ww_smoothing.ipynb` used in the [Nature Microbiology article](https://doi.org/10.1038/s41564-022-01185-x), posterior probabilities of the local haplotype generated by ShoRAH are not taken into account, and the curves are built using LolliPop's kernel based deconvolution which is both more robust against variants that share mutations in their exhaustive lists, and able to leverage the time component to  compensate the extreme over-dispersion of typical wastewater samples. See [LolliPop's preprint](https://doi.org/10.1101/2022.11.02.22281825) for details.

## Installation

Processing uses the V-pipe.
- branch: [ninjaturtles](https://github.com/cbg-ethz/V-pipe/tree/ninjaturtles), tip: [e8be5f1fad7a970e3299e142f329f037f3890fe4](https://github.com/cbg-ethz/V-pipe/commit/e8be5f1fad7a970e3299e142f329f037f3890fe4)
  - this branch relies on LolliPop 0.3 released on [bioconda](https://bioconda.github.io/recipes/lollipop/README.html).

Because the above is still in an experimental state, we run in a separate working area (`work-vp-test/` instead of `working/`), the prototype branch is in the [`V-pipe-test`](pangolin/V-pipe-test) submodule of repo pangolin. Scripts ([`cowabunga.sh`](https://github.com/cbg-ethz/pangolin/blob/master/cowabunga.sh)) assist handling these directories.


## Configuration

You still need to update manually `work-vp-test/var_dates.yaml` and re-run V-pipe if coocurrences have revealed early presence of another variant. See [LolliPop's README.md](https://github.com/cbg-ethz/LolliPop#run-the-deconvolution) for details.

- `/pangolin/work-vp-test/variant_config.yaml` -- general information (variants, locations) used for deconvolution
  - _locations_list_ (fomerly _cities_list_): full names of the locations for which to generate curves (see right column of `ww_locations.tsv`).
  - _variants_pangolin_ - dictionary mapping short names to the official [PANGO lineages](https://cov-lineages.org/) (see: "_pangolin:_" and "_short:_" fields in the `voc/`_*_`.yaml` description)
    - V-pipe will auto-generate such a list in `/pangolin/work-vp-test/variants/variants_pangolin.yaml` you can copy-paste the section)
  - _start_date_:  first  date for the deconvolution
  - _to_drop_: category of mutation to skip from tallymut (e.g.: `subset`),
  - (_variants_not_reported_ and _variants_list_ aren't provided manually anymore as LolliPop can autoguess them correctly)
- `/pangolin/work-vp-test/var_dates.yaml` -- which variants LolliPop needs to deconvolute for over which period of time.
  - at each starting date, list the combination of variants that will be deconvoluted for the next period of time, as determined by cojac in the section above.

Configuration file `regex.yaml` defines regular expressions that help parse the samples names as per section [Processing raw-reads with V-pipe](#processing-raw-reads-with-v-pipe) above.

- `sample` (and optionally `batch`) define regular expressions that are run against the first (and optionally second) column of V-pipe's `samples.tsv`. They define the following named-groups
  - `location`: this named-group gives the code for the location (e.g.: Ewag's number code, `Ba`, `KLZH`, etc.)
  - `year`: year (in `YYYY` or `YY` format. `YY` are automatically expanded to `20YY` --- Yes, I am optimistic with the duration of this pandemic. Or pessimistic with long term use of V-pipe after the turn of century ;-) ).
  - `month`: month
  - `day`: day
  - `date`: an alternative to the year/month/day groups, if dates aren't in a standard format.
  - regex are parsed with the [Python regex library](https://pypi.org/project/regex/), and multiple named groups can use the same name.
    You can thus have a construction where you use `|` to give multiple alternative as long as each provide named-groups `location` and either  `year`, `month`, and `day` or `date`:
    ```regex
    (?:(?P<location>\d+)_(?P<year>20\d{2})_(?:(?:(?P<month>[01]?\d)_(?P<day>[0-3]?\d))|(?:R_(?P<repeat>\d+))))|^(?:(?P<location>KLZHCo[vV])(?P<year>\d{2})(?P<month>[01]?\d)(?P<day>[0-3]?\d)(?:_(?P<location_extra>\w+))?)|^(?:(?P<location>B[aA])(?P<BAsam>\d{6})(?:[-_](?P<year>20\d{2})-(?P<month>[01]?\d)-(?P<day>[0-3]?\d))?)
    ```
    (I swear I have personally typed the line above. It has nothing to do with cats walking on my keyboard).
- `datefmt`: [strftime/strptime format string](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes) to be used on regex named group `date` (e.g.: use `"%Y%m%d"` to parse YYYYMMDD).
  - This is most useful for date formats that don't split nicely into the ` year`, `month`, and `day` regex  named groups: e.g. if your date format uses week number, day of the week, or day of year.
    In that case, write a regular expression that provides a named-group `date`, and then use, e.g., `%W%w` or `%j` in your ` datefmt`.

A look-up table `ww_locations.tsv` maps the location code (see `location` regex named group in the previous file) to their full description.

You can find a copy of these configuration in this repo.

## Analyzing wastewater with V-pipe

The following document assumes user have already performed the base analysis and the cooccurrence with V-pipe, but because Snakemake is dependency-based, it is also possible to automatically regenerate any intermediate output.

### Inputs

(the script will have already generated most of it for you)

- `/pangolin/work-vp-test/samples.wastewateronly.tsv` -- TSV table of the samples (the subset samples.tsv with wastewater samples)
- `/pangolin/work-vp-test/reference/voc/`_*_`.yaml` -- definition of the variants
  - a copy of this collection of YAML is in the [`voc/` subdirectory](voc/)
  - TODO procedure for creating and curating new one
- `/pangolin/work-vp-test/work-vp-results/`_*_`/`_*_`/alignment/basecnt.tsv.gz` -- Basecounts (pileup-like coverage plot) generated by V-pipe (see [base processing](#base-processing) above).
- `/pangolin/work-vp-test/references/gffs/Genes_NC_045512.2.GFF3` -- genes table  (used to add Gene names into the tallymut).
- `/pangolin/work-vp-test/deconv_bootstrap_cowwid.yaml` -- preset for running the deconvolution with bootstrapping to generate confidence intervals (slower).

> **Note** When variant curves approach 0, there are instabilities with the error margins generated by the current deconvolution methods when using Wald confidence interval. We use the slower bootstrap deconvolution preset instead.

### Execution

> **Summary:** actual processing is handled by V-pipe, here we document the exact commands that we use locally on our cluster.

Because the above is still in an experimental state, we run in a separate working area (`work-vp-test/` instead of `working/`, and the V-pip installed in `V-pipe-test/` instead of `V-pipe/`).

In the directory `pangolin`, there is a tool called `cowabunga.sh` (that can assist in preparing data for running V-pipe).

- run `./cowabunga.sh autoaddwastewater`
  - this adds the wastewater samples at top of file `/pangolin/work-vp-test/samples.wastewateronly.tsv`
- run `./cowabunga.sh bring_results`
  - this creates the necessary hard-links inside `/pangolin/work-vp-test/results` so that V-pipe can reuse the alignments previously done as part of the [base processing](#base-processing).
- submit V-pipe to the cluster with SLURM:
  - for interactive output on the terminal:
    ```bash
    cd work-vp-test/
    srun --pty --job-name=COWWID-vpipe --mem-per-cpu=4096 --mail-type=END --mail-user="ivan.topolsky@bsse.ethz.ch" --time=23:00:00 -- vpipe-test.sbatch
    ```
  - for batch submission:
    ```bash
    cd work-vp-test/
    sbatch vpipe-test.sbatch
    ```
  - > **Note** this will run both the cooccurrence and the deconvolution, see content of `vpipe-test.sbatch`:
    ```bash
    …
    exec ./vpipe --profile ${SNAKEMAKE_PROFILE} --restart-times=0 \
        allCooc variants/cohort_cooc_report.v41.csv tallymut deconvolution \
        --groups sigmut=group0 cooc=group1 \
        --group-components group0=10 group1=5
    ```
    to only run LolliPop use rules such as:
    - `tallymut` -- will run all the way to generating the heatmap-like structure (a tally of all mutations over dates and location) that serves as an input of the deconvolution.
    - `deconvolution` -- runs the deconvolution itself

### Output

- `/pangolin/work-vp-test/variants/tallymut.tsv.zstd` -- table of all variant-characteristic mutations found
- `/pangolin/work-vp-test/variants/deconvolute.tsv.zstd`  -- output of the deconvolution
- `/pangolin/work-vp-test/variants/deconvolute_upload.json` -- curves in a JSON format for uploading onto dashboards.



## Generate the plot: Heatmaps

> **Note** since switching to the exhaustive mutation list, the mutation heatmap display has become unusable and is not generated anymore.

> **Todo** better visualization of the presence of variants.


## Interpretation of results

Notebook [`DeconvolutionPrediagnostics.ipynb`](DeconvolutionPrediagnostics.ipynb) help diagnose problems related to data (drop-out affecting mutations) and/or signatures (too much similarity) that could affect the deconvolution.
> **Note** Previsualisation of the curves won't be done here, but is done before [uploading to dashboard](#upload) instead.

### Configuration

Configuration of the notebook relies on the same files `work-vp-test/variants.yaml` and `work-vp-test/var_dates.yaml` as used by V-pipe.

### Input

- `./work-vp-test/variants//tallymut.tsv.zst` -- table of all variant-characteristic mutations generated by V-pipe

### Execution

Run all cells of [DeconvolutionPrediagnostics.ipynb](DeconvolutionPrediagnostics.ipynb).

## Upload

Notebook [`ww_cov_uploader_V-pipe.ipynb`](ww_cov_uploader_V-pipe.ipynb) previsualizes the curves generated by V-pipe before uploading and handles the upload onto CoV-Spectrum and BAG/FOPH's dashboards.

### Input
- `/pangolin/work-vp-test/variants/deconvolute_upload.json` -- V-pipe generated curves in a JSON format for uploading onto dashboards.

In addition the actual upload itself requires database credentials. These are currently retrieved from `~/.netrc` standard Unix credential storage, but alternative methods are commented-out in the cells under the "Upload to Cov-Spectrum" section.

### Configuration

Configuration of graph colors and input/output path is in section "[Globals](ww_cov_uploader_V-pipe.ipynb#Globals)".

For better uniformity of all Swiss reporting, it is good practice to keep colors in sync between reports.
Check [upstream configuration of covariants.org](https://github.com/hodcroftlab/covariants/blob/master/web/data/clusters.json) for colors used by variants.
Conversely, send pull requests on [Cov-Spectrum's configuration file](https://github.com/GenSpectrum/cov-spectrum-website/blob/develop/src/models/wasteWater/constants.ts) to update colours of the dashboard.

### Execution

- Run up to and including "[Plot](ww_cov_uploader_V-pipe.ipynb#Plot)"
  - inspect the plots for anomalies.
  - Share the generated plot
- Run cells in section "[Upload to Cov-Spectrum](ww_cov_uploader_V-pipe.ipynb#Upload-to-Cov-Spectrum)" with the following:
  - the cell tagged "`## Abort DB update !`" is used only to abort the update and rollback to the initial state in case or problems. It is skipped otherwise.
  - the cell tagged "`## Save to DB !`" is used instead to make the changes permanent in the database.
- Run the remaining cells, section "[Upload to FOPH/BAG's Polybox](ww_cov_uploader_V-pipe.ipynb#Upload-to-FOPH/BAG's-Polybox)"

### Outputs

- `plots/combined-vpipe.pdf`-- previsualisation of the plots
- `ww_update_data_combined.json` -- back-up of the data before upload (note: as mentioned before, the heatmap part is currently empty).
- `/tmp/ww_update_data_smooth_kernel_rob.json` -- JSON reformated in the older format (order _variants_ => _locations_ => data, instead of the current _locations_ => _variants_ => data)

The curves are now loaded up on [CoV-Spectrum](https://cov-spectrum.ethz.ch/story/wastewater-in-switzerland).
The curves are now shared on Polybox for BAG/FOPH to pick up.


# Comments regarding the current procedure

Due to the excessively long list of mutations generated from Cov-Spectrum, and the excessively complex amplicon-cooccurrence that results of it, heatmaps aren't displayed anymore as they are unreadable. We are working toward fixing this.

Unlike the pre-print [doi:10.1101/2021.01.08.21249379](https://www.medrxiv.org/content/10.1101/2021.01.08.21249379), the current procedure skips running ShoRAH:  Instead of trying to build confidence at the level of single mutation, current method in LolliPop relies instead on a kernel-based deconvolution that enables us to leverage the time component and gives us higher confidence in our call despite drop-outs and extreme dispersion of data.

As an additional measure to avoid outliers, mutations which aren’t exclusive to a single variant aren’t taken into account in B.1.351/beta and P.1/gamma.
E.g.: mutation nuc: A23063T (aa: N501Y) will not be used there as it is also present in B.1.1.7/alpha and would artificially inflate the numbers.
Other similar signature mutations which do not follow the general trend of a variant are also filtered out.

'Undetermined' is defined by the absence of signature mutations, thus it doesn't have its own heatmap (it is defined by the complement of all other heatmaps).

The values of the curves are currently clipped to the [0;1] interval as the smoothing can currently generate values outside this range.

As the procedure is improved these caveats are subject to change in future revision of this document.
