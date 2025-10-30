# prepare_ohe_from_packbits.py
import os, argparse, numpy as np, sys

# Add path to import utilities
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'train'))
from utils import unpackbits_sequence

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--packbits", required=True)
    ap.add_argument("--indices", default=None, help="optional .npy of indices to subset")
    ap.add_argument("--seq-len", type=int, default=4096)
    ap.add_argument("--model-seq-len", type=int, default=4096)
    ap.add_argument("--out", required=True, help="path to write ohe.npz")
    ap.add_argument("--batch-size", type=int, default=128)
    args = ap.parse_args()

    seqs = np.load(args.packbits)
    if args.indices:
        seqs = seqs[np.load(args.indices)]
    N = len(seqs)
    L_full, L = args.seq_len, args.model_seq_len
    center, half = L_full // 2, L // 2

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    memmap_path = os.path.join(os.path.dirname(args.out), "ohe.tmp.memmap")
    ohe = np.memmap(memmap_path, dtype=np.float32, mode="w+", shape=(N, 4, L))

    B = args.batch_size
    for s in range(0, N, B):
        e = min(N, s + B)
        b = unpackbits_sequence(seqs[s:e], L_full)    # [b, L_full, 4]
        b = b[:, center - half:center + half, :]      # [b, L, 4]
        b = b.transpose(0, 2, 1).astype(np.float32)   # [b, 4, L]
        ohe[s:e] = b
    del ohe

    arr = np.memmap(memmap_path, dtype=np.float32, mode="r", shape=(N, 4, L))
    np.savez_compressed(args.out, arr_0=np.array(arr))
    del arr
    os.remove(memmap_path)
    print(f"Wrote {args.out}")

if __name__ == "__main__":
    main()

