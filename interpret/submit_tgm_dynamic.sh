#!/usr/bin/env bash
set -euo pipefail

# IMPORTANT: Update MAIL_USER and other SLURM settings below for your system
# Set environment variables before running, or edit defaults here

# --- Your inputs ---
PACKBITS=${PACKBITS:-./data/test.seqs_packbits.seed=121.gt_0.9.npy}
CKPT=${CKPT:-./models/hedgehog.pth}
OUTDIR=${OUTDIR:-./data/hedgehog/tgm/e1_gt_0.9}
TARGETS_FILE=${TARGETS_FILE:-./data/e1_hedgehog_inds.txt}

# --- Tangermeme run settings ---
N_TARGETS=${N_TARGETS:-296}
MODEL_SEQ_LEN=${MODEL_SEQ_LEN:-2048}
TARGETS_PER_JOB=${TARGETS_PER_JOB:-25}
N_SHUFFLES=${N_SHUFFLES:-16}
PAIR_BATCH_SIZE=${PAIR_BATCH_SIZE:-64}
EXAMPLES_PER_CALL=${EXAMPLES_PER_CALL:-2048}
REF_KIND=${REF_KIND:-dinuc_full}
SAVE_DTYPE=${SAVE_DTYPE:-float32}
COMPRESSION=${COMPRESSION:-lzf}

# --- SLURM resources ---
PARTITION=${PARTITION:-gpu}
GRES=${GRES:---gres=gpu:1}
CONSTRAINT=${CONSTRAINT:---constraint=a100}
MEM=${MEM:-50G}
CPUS=${CPUS:-8}
TIME=${TIME:-48:00:00}
CONCURRENCY=${CONCURRENCY:-4}
MAIL_USER=${MAIL_USER:-kchen@flatironinstitute.org}  # UPDATE: Change to your email
MAIL_TYPE=${MAIL_TYPE:-FAIL}

# Compute number of shards from lines in TARGETS_FILE
if [[ ! -s "$TARGETS_FILE" ]]; then
  echo "ERROR: TARGETS_FILE not found or empty: $TARGETS_FILE" >&2
  exit 1
fi
NUM_TARGETS=$(grep -cve '^[[:space:]]*$' "$TARGETS_FILE")
NUM_SHARDS=$(( (NUM_TARGETS + TARGETS_PER_JOB - 1) / TARGETS_PER_JOB ))
ARRAY_SPEC="0-$((NUM_SHARDS-1))%${CONCURRENCY}"

echo "Found $NUM_TARGETS targets in $TARGETS_FILE"
echo "Submitting array: $ARRAY_SPEC  (targets/job=$TARGETS_PER_JOB)"

sbatch \
  --job-name=tgm-dlift \
  --time="$TIME" \
  --partition="$PARTITION" \
  $GRES \
  $CONSTRAINT \
  --mem="$MEM" \
  -c "$CPUS" \
  --array="$ARRAY_SPEC" \
  --mail-user="$MAIL_USER" \
  --mail-type="$MAIL_TYPE" \
  --export=ALL,PACKBITS="$PACKBITS",CKPT="$CKPT",OUTDIR="$OUTDIR",TARGETS_FILE="$TARGETS_FILE",\
N_TARGETS="$N_TARGETS",MODEL_SEQ_LEN="$MODEL_SEQ_LEN",TARGETS_PER_JOB="$TARGETS_PER_JOB",\
N_SHUFFLES="$N_SHUFFLES",PAIR_BATCH_SIZE="$PAIR_BATCH_SIZE",EXAMPLES_PER_CALL="$EXAMPLES_PER_CALL",\
REF_KIND="$REF_KIND",SAVE_DTYPE="$SAVE_DTYPE",COMPRESSION="$COMPRESSION" \
  <<'SBATCH_SCRIPT'
#!/bin/bash
#SBATCH -J hedgehog-dlift-296
module purge || true
source ~/.bashrc
conda activate sei-modisco

mkdir -p "$OUTDIR"

srun python -u deeplift_tgm_baselines.py \
  --packbits "$PACKBITS" \
  --checkpoint "$CKPT" \
  --n-targets "$N_TARGETS" \
  --outdir "$OUTDIR" \
  --targets-file "$TARGETS_FILE" \
  --targets-per-job "$TARGETS_PER_JOB" \
  --n-shuffles "$N_SHUFFLES" \
  --pair-batch-size "$PAIR_BATCH_SIZE" \
  --examples-per-call "$EXAMPLES_PER_CALL" \
  --ref-kind "$REF_KIND" \
  --model-seq-len "$MODEL_SEQ_LEN" \
  --save-dtype "$SAVE_DTYPE" \
  --compression "$COMPRESSION" \
  --device cuda \
  --save-ohe
SBATCH_SCRIPT

