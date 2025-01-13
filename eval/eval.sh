#!/bin/bash
#SBATCH --time=2-00:00:00
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --constraint=a100
#SBATCH --mem=64000
#SBATCH --mail-user=kchen@flatironinstitute.org
#SBATCH --mail-type=ALL

python3 -u ./get_model_predictions.py --config=./eval.yaml \
                                      --dataset=$1 \
                                      --outdir=$2
