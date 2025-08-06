#!/bin/bash
#SBATCH --job-name="COVID-vpipe-hugemem"
#SBATCH --mail-user=$(cat slurm_email_recipients)
#SBATCH --mail-type=END
#SBATCH --mem-per-cpu=16384
#SBATCH --oversubscribe
#SBATCH --time=6:00:00

umask 0007

# unlock if crashed before finishing
sleep 300
./vpipe --configfile config.unlock.yaml ---dryrun --unlock

mkdir -p cluster_logs/
export SNAKEMAKE_PROFILE=$(realpath ../profiles/)
exec ./vpipe --profile ${SNAKEMAKE_PROFILE}/custom-lsf/ --configfile config.hugemem.yaml
