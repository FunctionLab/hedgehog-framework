#!/bin/bash
#SBATCH --time=5-00:00:00
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --constraint=a100
#SBATCH --mem 60G
#SBATCH -o fasta_%j.out
#SBATCH --mail-user=kchen@flatironinstitute.org
#SBATCH --mail-type=FAIL

set -o errexit
set -o pipefail
set -o nounset

fasta_filepath="${1:-}"
out_dir="${2:-}"

mkdir -p $out_dir

echo "Input arguments: $fasta_filepath $out_dir"

python3 -u ./fasta.py --yaml=./fasta.yaml \
                      --fasta=$fasta_filepath \
                      --output-dir=$out_dir \
                      --cuda
