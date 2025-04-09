#!/bin/bash
#SBATCH --job-name=snakerunner
#SBATCH --time='48:00:00'
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=logs/%x-%j.txt

module load singularity-ce
profile=$1
shift
echo "profile: $profile"
snakemake -p $@ --profile $profile
