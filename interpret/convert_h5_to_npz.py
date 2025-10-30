# convert_h5_to_npz.py
import os, glob, argparse, h5py, numpy as np

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", required=True, help="dir containing t*.h5 with dataset hyp_contribs")
    ap.add_argument("--out-dir", required=True, help="dir to write hypcontribs_t*.npz")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    paths = sorted(glob.glob(os.path.join(args.in_dir, "t*.h5")))
    assert paths, f"No t*.h5 in {args.in_dir}"
    for h5p in paths:
        t = os.path.splitext(os.path.basename(h5p))[0]  # "t123"
        outp = os.path.join(args.out_dir, f"hypcontribs_{t}.npz")
        if os.path.exists(outp) and not args.force:
            continue
        with h5py.File(h5p, "r") as f:
            arr = f["hyp_contribs"][:]  # [N,4,L]
        np.savez_compressed(outp, arr_0=arr)
        print("Wrote", outp)

if __name__ == "__main__":
    main()

