#!/bin/bash
#SBATCH --time=7-00:00:00
#SBATCH --partition=gpu
#SBATCH --gres=gpu:4
#SBATCH --constraint=a100
#SBATCH -n 16
#SBATCH --mem=64000
#SBATCH --mail-user=kchen@flatironinstitute.org
#SBATCH --mail-type=ALL

python3 -u ./train.py --config=$1 \
                      --lr=0.01
