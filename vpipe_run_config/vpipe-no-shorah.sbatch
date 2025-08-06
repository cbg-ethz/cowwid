#!/bin/bash
#SBATCH --job-name="COVID-vpipe-cons"
#SBATCH --mail-user=$(cat slurm_email_recipients)
#SBATCH --mail-type=END
#SBATCH --mem-per-cpu=16384
#SBATCH --oversubscribe
#SBATCH --time=3:00:00
#SBATCH --comment="batches	@TAG@"


logfile=/cluster/scratch/bs-pangolin/log.$LSB_JOBID

# tee all output from this script into logfile
exec > >(tee -a $logfile) 2>&1

set -e

umask 0007

# unlock if crashed before finishing
./vpipe --configfile config.unlock.yaml --dryrun --unlock || exit 1
#--cleanup-shadow

# update the shared snake envs (with proxy when not on a login node)
#./create_envs -p
# proxy so update can work
echo "Using proxy"
#. /etc/profile.d/software_stack_default.sh
module load eth_proxy
echo "${https_proxy}"

mkdir -p cluster_logs/
export SNAKEMAKE_PROFILE=$(realpath ../profiles/smk-simple-slurm/ )
./vpipe --profile ${SNAKEMAKE_PROFILE}	\
	--configfile config.no-shorah.yaml --omit-from snv
