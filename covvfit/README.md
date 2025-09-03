3.9.2025 kkirschen
The purpose of this folder is to run the covvfit analyisis discribed in htis tutorial: https://github.com/cbg-ethz/covvfit/blob/main/docs/running_deconv/lollipop.md

**Disclaimer** 
the lollipop installation used for regular processing in in vpipe. This repo is only an **intermediate** solution until covvfit will be a rule provided by vpipe.
Thus, also the Lollipop installation should be **removed** once covvit is integrated in v-pipe!

# Folder strucutre
- analysis: store the config, scripts and results
- envs: store the conda env needed to run covvid (incl. lollipop)
- git: stores the lollipop installation to run covvfit

# Procedure
1. regular processing incl. lollipop run --> this provides the updated files (e.g. tallymut.tsv) to run the **second** lollipop here without smoothing
2. rerun lollipop with: `/cluster/project/pangolin/cowwid/covvfit/analysis/lollipop/scripts/run_covvfit_lollipop.sh`
3. run covvfit with: `/cluster/project/pangolin/cowwid/covvfit/analysis/covvfit_analysis/scripts/run_covvfit.sh`
