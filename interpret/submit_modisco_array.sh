#!/usr/bin/env bash
set -euo pipefail

# Paths (edit as needed)
OHE=${OHE:-./data/sei/ohe/ohe.gt_0.9.npz}
NPZ_DIR=${NPZ_DIR:-./data/sei/npz/e1_gt_0.9}
OUT_DIR=${OUT_DIR:-./data/sei/modisco/e1_gt_0.9}
REPORT_DIR=${REPORT_DIR:-./data/sei/reports/e1_gt_0.9}

# Resources
TIME=${TIME:-12:00:00}
PARTITION=${PARTITION:-ccb}
MEM=${MEM:-64G}
CPUS=${CPUS:-8}
CONCURRENCY=${CONCURRENCY:-16}
MODISCO_W=${MODISCO_W:-400}
MODISCO_N=${MODISCO_N:-2000}

mkdir -p "$OUT_DIR" "$REPORT_DIR"

# Build a frozen, sorted task list
TASKLIST="${NPZ_DIR%/}/.modisco_tasklist.txt"
find "$NPZ_DIR" -maxdepth 1 -type f -name 'hypcontribs_*.npz' -print0 \
  | sort -z -V \
  | xargs -0 -n1 -I{} echo "{}" > "$TASKLIST"

NUM=$(wc -l < "$TASKLIST" | tr -d ' ')
if [[ "$NUM" -eq 0 ]]; then
  echo "No NPZ files in $NPZ_DIR"; exit 1
fi
ARRAY="0-$((NUM-1))%${CONCURRENCY}"
echo "Submitting array: $ARRAY (files: $NUM)"

sbatch \
  --job-name=modisco-subset \
  --time="$TIME" \
  --partition="$PARTITION" \
  --cpus-per-task="$CPUS" \
  --mem="$MEM" \
  --array="$ARRAY" \
  --export=ALL,OHE="$OHE",OUT_DIR="$OUT_DIR",REPORT_DIR="$REPORT_DIR",TASKLIST="$TASKLIST",MODISCO_W="$MODISCO_W",MODISCO_N="$MODISCO_N" \
  modisco_array.sh

