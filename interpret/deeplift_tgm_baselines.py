import os, argparse, numpy as np, h5py, torch, sys
from selene_sdk.utils import NonStrandSpecific

# Add paths to import Wreath model and utilities
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'model'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'train'))
from wreath import Wreath
from utils import init_weights, unpackbits_sequence

# tangermeme
from tangermeme.deep_lift_shap import deep_lift_shap
from tangermeme.ersatz import dinucleotide_shuffle

def disable_inplace_relu(model):
    """Recursively set inplace=False for all ReLU layers"""
    for module in model.modules():
        if isinstance(module, torch.nn.ReLU):
            module.inplace = False
    return model

def load_model(checkpoint_path, seq_len, n_targets, device, use_rc=False):
    ckpt = torch.load(checkpoint_path, map_location=lambda storage, location: storage)
    base = Wreath(sequence_length=seq_len, n_genomic_features=n_targets)
    model = NonStrandSpecific(base) if use_rc else base
    model = init_weights(model, ckpt).to(device).eval()

    model = disable_inplace_relu(model)

    # sanity
    with torch.no_grad():
        y = model(torch.zeros(2,4,seq_len,device=device))
        assert list(y.shape)==[2,n_targets], f"Unexpected output shape {y.shape}"
    return model

def shard_targets(all_targets, per_job, task_id):
    s = task_id*per_job; e = min(len(all_targets), s+per_job)
    return all_targets[s:e]

def open_writer(path, N, L, chunk_b, compression, dtype):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    f = h5py.File(path, 'w')
    dset = f.create_dataset('hyp_contribs', shape=(N,4,L), dtype=dtype,
                            chunks=(min(chunk_b,N),4,L),
                            compression=(None if compression=='none' else compression))
    return f, dset

def build_references_factory(args, L):
    """Return ('function', fn) or ('tensor', arr) for tangermeme's references=..."""
    if args.ref_kind == "dinuc_full":
        def _fn(X, n, random_state=None):
            # Don't pass start/end at all, let function use defaults
            return dinucleotide_shuffle(X, n=n, random_state=random_state)
        return "function", _fn
    if args.ref_kind == "dinuc_window":
        s = None if args.shuffle_start<0 else args.shuffle_start
        e = None if args.shuffle_end<0 else args.shuffle_end
        def _fn(X, n, random_state=None):
            # Only pass start/end if they have actual values
            kwargs = {'n': n, 'random_state': random_state}
            if s is not None:
                kwargs['start'] = s
            if e is not None:
                kwargs['end'] = e
            return dinucleotide_shuffle(X, **kwargs)
        return "function", _fn
    if args.ref_kind == "uniform025":
        def _fn(X, n, random_state=None):
            return torch.full((X.shape[0], n, 4, X.shape[2]), 0.25, dtype=X.dtype, device=X.device)
        return "function", _fn
    if args.ref_kind == "zeros":
        def _fn(X, n, random_state=None):
            return torch.zeros((X.shape[0], n, 4, X.shape[2]), dtype=X.dtype, device=X.device)
        return "function", _fn
    if args.ref_kind == "from_file":
        assert args.ref_path, "--ref-path required for ref_kind=from_file"
        R = np.load(args.ref_path)
        key = "arr" if isinstance(R, np.lib.npyio.NpzFile) and "arr" in R.files else (R.files[0] if hasattr(R,'files') else None)
        R = R[key] if key is not None else R
        assert R.ndim==4 and R.shape[2]==4 and R.shape[3]==L, f"Expected refs (N,n_refs,4,L), got {R.shape}"
        return "tensor", R
    raise ValueError("Unknown ref_kind")

def main():
    ap = argparse.ArgumentParser()
    # data
    ap.add_argument("--packbits", required=True)
    ap.add_argument("--indices", default=None)
    ap.add_argument("--seq-len", type=int, default=4096)
    ap.add_argument("--model-seq-len", type=int, default=4096)
    # model
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--n-targets", type=int, default=296)
    ap.add_argument("--use-rc", action="store_true")
    # targets
    ap.add_argument("--targets-file", default=None)
    ap.add_argument("--targets-per-job", type=int, default=25)   # smaller, since each target is single-pass
    # tangermeme settings
    ap.add_argument("--n-shuffles", type=int, default=16)
    ap.add_argument("--pair-batch-size", type=int, default=64)   # example-ref pairs per GPU step
    ap.add_argument("--random-state", type=int, default=0)
    ap.add_argument("--ref-kind", choices=["dinuc_full","dinuc_window","uniform025","zeros","from_file"], default="dinuc_full")
    ap.add_argument("--shuffle-start", type=int, default=-1, help="start idx for dinuc_window; -1 => None")
    ap.add_argument("--shuffle-end", type=int, default=-1, help="end idx (exclusive) for dinuc_window; -1 => None")
    ap.add_argument("--ref-path", default=None, help="npz/npy with refs (N,n_refs,4,L) if ref_kind=from_file")
    # streaming & IO
    ap.add_argument("--examples-per-call", type=int, default=2048)
    ap.add_argument("--batch-size", type=int, default=128)       # used only for ohe save
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--save-dtype", choices=["float32","float16"], default="float32")
    ap.add_argument("--compression", choices=["lzf","gzip","none"], default="lzf")
    ap.add_argument("--save-ohe", action="store_true")
    # device
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    seqs = np.load(args.packbits)
    if args.indices: seqs = seqs[np.load(args.indices)]
    N = len(seqs)
    L_full, L = args.seq_len, args.model_seq_len
    c, h = L_full//2, L//2

    # targets
    if args.targets_file and os.path.exists(args.targets_file):
        with open(args.targets_file) as f:
            all_targets = [int(x.strip()) for x in f if x.strip()]
    else:
        all_targets = list(range(args.n_targets))
    tid = int(os.environ.get("SLURM_ARRAY_TASK_ID","0"))
    shard = shard_targets(all_targets, args.targets_per_job, tid)
    if not shard:
        print(f"[Task {tid}] no targets"); return
    print(f"[Task {tid}] N={N} targets={len(shard)} (first few {shard[:6]})")

    # model
    model = load_model(args.checkpoint, L, args.n_targets, device, use_rc=args.use_rc)

    # references
    ref_mode, refs_obj = build_references_factory(args, L)

    # optional ohe
    if args.save_ohe and tid==0:
        ohe_path = os.path.join(args.outdir,"ohe.npz")
        if not os.path.exists(ohe_path):
            tmp = np.memmap(os.path.join(args.outdir,'ohe.tmp.memmap'),
                            dtype=np.float32, mode='w+', shape=(N,4,L))
            B = args.batch_size
            for s in range(0,N,B):
                e = min(N,s+B)
                b = unpackbits_sequence(seqs[s:e], L_full)            # [b,Lfull,4]
                b = b[:, c-h:c+h, :].transpose(0,2,1).astype(np.float32)
                tmp[s:e] = b
            del tmp
            arr = np.memmap(os.path.join(args.outdir,'ohe.tmp.memmap'),
                            dtype=np.float32, mode='r', shape=(N,4,L))
            np.savez_compressed(ohe_path, arr=np.array(arr)); del arr
            os.remove(os.path.join(args.outdir,'ohe.tmp.memmap'))

    os.makedirs(args.outdir, exist_ok=True)
    out_dtype = np.float32 if args.save_dtype=='float32' else np.float16

    # loop targets
    for t in shard:
        out_h5 = os.path.join(args.outdir, f"t{t}.h5")
        if os.path.exists(out_h5):
            with h5py.File(out_h5,'r') as f:
                if 'hyp_contribs' in f and tuple(f['hyp_contribs'].shape)==(N,4,L):
                    print(f"t{t}: exists, skipping."); continue
            os.remove(out_h5)

        print(f"t{t}: writing {out_h5}")
        f, dset = open_writer(out_h5, N, L, args.examples_per_call, args.compression, out_dtype)

        for s in range(0, N, args.examples_per_call):
            e = min(N, s+args.examples_per_call)
            b = unpackbits_sequence(seqs[s:e], L_full)                 # [b,Lfull,4]
            b = b[:, c-h:c+h, :].transpose(0,2,1).astype(np.float32)   # [b,4,L]
            X = torch.from_numpy(b)  # CPU; tangermeme moves pairs to device

            if ref_mode == "function":
                refs = refs_obj  # function reference
                nrefs = args.n_shuffles
            else:
                chunk_refs = refs_obj[s:e]                              # [b,n_refs,4,L]
                refs = torch.from_numpy(chunk_refs) if isinstance(chunk_refs, np.ndarray) else chunk_refs
                nrefs = refs.shape[1]

            X_attr = deep_lift_shap(
                model, X, target=t,
                n_shuffles=nrefs,
                references=refs,
                device=args.device,
                batch_size=args.pair_batch_size,
                random_state=args.random_state
            )  # [b,4,L] torch

            arr = X_attr.detach().cpu().numpy()
            if out_dtype is np.float16: arr = arr.astype(np.float16)
            dset[s:e, :, :] = arr

            del X_attr, X, arr

        f.close()

    print("Done.")

if __name__ == "__main__":
    main()

