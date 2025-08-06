#!/bin/bash
#SBATCH --job-name="COVID-vpipe"
#SBATCH --mail-user=$(cat slurm_email_recipients)
#SBATCH --mail-type=END
#SBATCH --mem-per-cpu=16384
#SBATCH --oversubscribe
#SBATCH --time=3:00:00

umask 0007

mkdir -p cluster_logs/
./vpipe --configfile config.snv.yaml --dryrun --unlock
# export SNAKEMAKE_PROFILE=$(realpath ../profiles/custom-lsf/)
# exec ./vpipe --profile ${SNAKEMAKE_PROFILE}	\
export SNAKEMAKE_PROFILE=$(realpath ../profiles/smk-simple-slurm/ )
exec ./vpipe --profile ${SNAKEMAKE_PROFILE}	\
	--configfile config.snv.yaml
