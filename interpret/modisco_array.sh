#!/bin/bash
#SBATCH -J modisco-one
# Do NOT set --array here; wrapper passes it dynamically.
# IMPORTANT: This script is called by submit_modisco_array.sh

set -euo pipefail
: "${TASKLIST:?TASKLIST not set}"
: "${OHE:?OHE not set}"
: "${OUT_DIR:?OUT_DIR not set}"
: "${REPORT_DIR:?REPORT_DIR not set}"
: "${MODISCO_W:?}"
: "${MODISCO_N:?}"

IDX="${SLURM_ARRAY_TASK_ID:?}"
A_NPZ="$(sed -n "$((IDX+1))p" "$TASKLIST")"
if [[ -z "$A_NPZ" || ! -s "$A_NPZ" ]]; then
  echo "Index $IDX has no file; exiting."; exit 0
fi

BASE="$(basename "$A_NPZ")"
ID="$(echo "$BASE" | sed -E 's/.*_t([0-9]+)\.npz/\1/;t; s/[^0-9]*([0-9]+).*/\1/')"
[[ -z "$ID" ]] && { echo "Cannot extract id from $BASE"; exit 1; }

OUT_H5="${OUT_DIR}/modisco_t${ID}.h5"
REP_DIR="${REPORT_DIR}/t${ID}"
mkdir -p "$REP_DIR"

# Canonicalize NPZ to 'arr_0' and check shapes
CANON_NPZ="$(mktemp --suffix=.npz)"
python - <<'PY' "$OHE" "$A_NPZ" "$CANON_NPZ"
import sys, numpy as np
def first_arr(p):
    z = np.load(p)
    if isinstance(z, np.lib.npyio.NpzFile):
        k = 'arr_0' if 'arr_0' in z.files else ('arr' if 'arr' in z.files else z.files[0])
        return z[k]
    return z
X = first_arr(sys.argv[1]); A = first_arr(sys.argv[2])
assert X.ndim==3 and X.shape[1]==4, f"ohe must be (N,4,L), got {X.shape}"
assert A.shape==X.shape, f"attrs {A.shape} must match ohe {X.shape}"
np.savez_compressed(sys.argv[3], arr_0=A.astype(np.float32, copy=False))
PY

echo "[$(date)] t${ID} :: running modisco"
modisco motifs -s "$OHE" -a "$CANON_NPZ" -o "$OUT_H5" -n "$MODISCO_N" -w "$MODISCO_W"
modisco report -i "$OUT_H5" -o "$REP_DIR" -s "$REP_DIR"
rm -f "$CANON_NPZ"
echo "[$(date)] t${ID} :: done"

